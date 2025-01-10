import logging
from itertools import groupby
from typing import Any, Dict, Optional, Set, Tuple
# from pprint import pprint

import odm_validation.part_tables as pt
import odm_validation.reports as reports
from odm_validation.input_data import DataKind
from odm_validation.reports import ErrorKind, ValidationCtx, get_row_num
from odm_validation.rule_filters import RuleFilter
from odm_validation.rules import Rule, RuleId, get_anyof_constraint, ruleset
from odm_validation.schemas import CerberusSchema, init_table_schema
from odm_validation.stdext import (
    countdown,
    deep_update,
    flatten,
)

RuleError = Tuple[RuleId, dict]


def _gen_cerb_rule_map():
    # Generates a dictionary that maps a cerberus validation rule to the ODM
    # rule that uses it.
    # Assumes that each cerberus validation can be mapped to one ODM validation
    # rule with no repetations.
    result = {}
    for r in ruleset:
        for key in r.keys:
            assert key not in result
            result[key] = r
            if not r.match_all_keys:
                break
    return result


def _is_invalid_type_rule(rule):
    return rule.id == RuleId.invalid_type


# local constants
_KEY_RULES = _gen_cerb_rule_map()

# local globals
_invalid_type_rule = next(filter(_is_invalid_type_rule, ruleset), None)


def _get_rule_id(x) -> RuleId:
    strval = x['ruleID']
    return RuleId[strval]


def _get_dataType(x):
    return x[pt.DATA_TYPE]


def _transform_rule(rule: Rule, column_meta) -> Rule:
    '''Returns a new rule, depending on `column_meta`.'''
    # XXX: dependency on meta value (which is only supposed to aid debug)
    # XXX: does not handle rules with match_all_keys enabled

    '''cerberus 'allowed' -> invalid_type, when dataType is boolean'''
    if rule.keys[0] == 'allowed':
        new_rule = _invalid_type_rule
        rule_ids = list(map(_get_rule_id, column_meta))
        if not new_rule or (new_rule.id not in rule_ids):
            return rule
        ix = rule_ids.index(new_rule.id)
        if pt.BOOLEAN in map(_get_dataType, column_meta[ix]['meta']):
            return new_rule

    return rule


def _get_allowed_values(cerb_rules: Dict[str, Any]) -> Set[str]:
    return set(cerb_rules.get('allowed', []))


def _extract_datatype(column_meta: list) -> Optional[str]:
    # XXX: depends on meta (which should only be for debug)
    assert column_meta is not None
    rule_metas = flatten(map(lambda x: x.get('meta', []), column_meta))
    datatype_metas = filter(lambda x: pt.DATA_TYPE in x, rule_metas)
    odm_type = next(datatype_metas, {}).get(pt.DATA_TYPE)
    return odm_type


def _get_rule_for_cerb_key(key: str, column_meta) -> Optional[Rule]:
    rule = _KEY_RULES.get(key)
    if not rule:
        logging.error(f'missing handler for cerberus rule "{key}"')
        return
    return _transform_rule(rule, column_meta)


def _cerb_to_odm_type(cerb_type: str) -> Optional[str]:
    t = cerb_type
    if t in {'boolean', 'datetime', 'integer', 'float'}:
        return t


def _gen_error_entry(vctx, cerb_rule, table_id, column_id, value, row_numbers,
                     rows, column_meta, rule_filter: RuleFilter,
                     constraint=None, schema_column=None,
                     data_kind=DataKind.python
                     ) -> Optional[RuleError]:
    "Generates a single validation error from input params."
    assert column_meta is not None
    if not value and cerb_rule == 'type':
        return

    rule = _get_rule_for_cerb_key(cerb_rule, column_meta)
    if not (rule and rule_filter.enabled(rule)):
        return

    # Only report column errors for the first line in spreadsheets.
    # It will always trigger on the first line do to how csv-files are
    # imported.
    if rule.is_column and data_kind == DataKind.spreadsheet:
        first_row_num = get_row_num(0, 0, data_kind)
        assert len(row_numbers) == 1
        if row_numbers[0] > first_row_num:
            return

    cerb_type = schema_column.get('type', None) if schema_column else None
    odm_type = _extract_datatype(column_meta)
    datatype = odm_type or _cerb_to_odm_type(cerb_type)

    allowed = _get_allowed_values(schema_column) if schema_column else []
    kind = ErrorKind.WARNING if rule.is_warning else ErrorKind.ERROR
    error_ctx = reports.ErrorCtx(
        allowed_values=allowed,
        column_id=column_id,
        column_meta=column_meta,
        constraint=constraint,
        err_template=rule.get_error_template(value, datatype, data_kind),
        row_numbers=row_numbers,
        rows=rows, value=value,
        rule_id=rule.id,
        table_id=table_id,
        data_kind=data_kind,
        is_column=rule.is_column,
        verbosity=vctx.verbosity,
    )
    entry = reports.gen_rule_error(error_ctx, kind)
    return (rule.id, entry)


def _get_cerb_rule(e):
    rule = e.schema_path[-1]

    # 'anyof' may be used to wrap the actual rule together with 'empty'
    if rule == 'anyof':
        (key, _) = get_anyof_constraint(e.constraint[0])
        rule = key

    return rule


def _gen_cerb_error_entry(vctx, e, row, schema: CerberusSchema,
                          rule_filter: RuleFilter, offset: int,
                          data_kind: DataKind) -> Optional[RuleError]:
    "Transforms a single Cerberus error into a validation error."
    cerb_rule = _get_cerb_rule(e)
    (table_id, _, column_id) = e.document_path
    row_index = e.document_path[1]
    schema_column = schema[table_id]['schema']['schema'][column_id]
    column_meta = schema_column.get('meta', [])
    row_numbers = [get_row_num(row_index, offset, data_kind)]
    rows = [row]
    assert column_meta is not None
    return _gen_error_entry(
        vctx,
        cerb_rule,
        table_id,
        column_id,
        e.value,
        row_numbers,
        rows,
        column_meta,
        rule_filter,
        e.constraint,
        schema_column,
        data_kind=data_kind,
    )


def _gen_aggregated_error_entry(vctx, agg_error, rule_filter: RuleFilter
                                ) -> Optional[dict]:
    """Transforms a single aggregated error (from OdmValidator) to a validation
    error."""
    return _gen_error_entry(
        vctx,
        agg_error.cerb_rule,
        agg_error.table_id,
        agg_error.column_id,
        agg_error.value,
        agg_error.row_numbers,
        agg_error.rows,
        agg_error.column_meta,
        rule_filter,
    )


def _get_table_name(x):
    return x['tableName']


def _get_row_num(x):
    return x.get('rowNumber') or x.get('rowNumbers')


def _get_column_name(x):
    return x['columnName']


def _get_error_rule_id(x) -> RuleId:
    assert 'errorType' in x, x
    strval = x['errorType']
    return RuleId[strval]


def _get_table_rownum_column(x):
    row_num = _get_row_num(x)
    if row_num is not None and isinstance(row_num, list):
        row_num = row_num[0]
    return (_get_table_name(x), _get_column_name(x), row_num)


def _sort_errors(errors):
    """Sorts errors by table, row-num, column."""
    return sorted(errors, key=_get_table_rownum_column)


def filter_errors(errors):
    """Removes redundant errors."""
    # This function currently only removes redundant _coercion errors produced
    # by `invalid_type`.
    #
    # Errors are deleted in reverse order to keep the two lists in sync.
    result = []
    sorted_errors = _sort_errors(errors)
    for tableName, table_errors in groupby(sorted_errors, _get_table_name):
        for rowNum, row_errors in groupby(table_errors, _get_row_num):
            for columnName, col_errors in groupby(row_errors,
                                                  _get_column_name):
                value_errors = list(col_errors)
                rule_ids = list(map(_get_error_rule_id, value_errors))
                if RuleId.invalid_type in rule_ids:
                    for i in countdown(len(value_errors)):
                        if rule_ids[i] == RuleId._coercion:
                            del value_errors[i]
                result += value_errors
    return result


def map_cerb_errors(vctx: ValidationCtx, table_id, cerb_errors, schema,
                    rule_filter, offset: int, data_kind):
    """Transforms Cerberus errors to validation errors (and warnings).

    :return: a pair of lists (errors, warnings).
    """
    errors = []
    warnings = []
    for table_error in cerb_errors:
        for row_errors in table_error.info:
            for e in row_errors:
                row = e.value
                for attr_errors in e.info:
                    for e in attr_errors:
                        rule_error = _gen_cerb_error_entry(vctx, e, row,
                                                           schema, rule_filter,
                                                           offset, data_kind)
                        if not rule_error:
                            continue
                        (rule_id, entry) = rule_error
                        if 'warningType' in entry:
                            warnings.append(entry)
                        else:
                            errors.append(entry)
    return errors, warnings


def map_aggregated_errors(vctx, table_id, agg_errors, rule_filter):
    """Transforms a list of aggregated errors from OdmValidator to a list of
    validation errors."""
    errors = []
    for ae in agg_errors:
        rule_error = _gen_aggregated_error_entry(vctx, ae, rule_filter)
        if not rule_error:
            continue
        (rule_id, entry) = rule_error
        errors.append(entry)
    return errors


def gen_additions_schema(additions) -> CerberusSchema:
    # This may work for all rules, but 'allowed' is the only officially
    # supported one.
    result = {}
    for table_id, attributes in additions.items():
        attr_schema = attributes
        table_schema = init_table_schema(table_id, [], attr_schema)
        deep_update(result, table_schema)
    return result
