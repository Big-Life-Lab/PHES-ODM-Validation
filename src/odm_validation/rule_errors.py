import logging
from itertools import groupby
from typing import Optional, Union, cast
# from pprint import pprint

from cerberus.errors import ValidationError

import odm_validation.part_tables as pt
import odm_validation.reports as reports
from odm_validation.part_tables import ColMeta, Meta, MetaEntry, SomeValue
from odm_validation.cerberusext import AggregatedError
from odm_validation.input_data import DataKind
from odm_validation.reports import ErrorKind, ValidationCtx, get_row_num
from odm_validation.rule_filters import RuleFilter
from odm_validation.rules import Rule, RuleId, get_anyof_constraint, ruleset
from odm_validation.schemas import CerberusSchema, Schema, init_table_schema
from odm_validation.stdext import (
    countdown,
    deep_update,
)

RuleError = tuple[RuleId, dict]


def _gen_cerb_rule_map() -> dict[str, Rule]:
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


def _is_invalid_type_rule(rule: Rule) -> bool:
    return rule.id == RuleId.invalid_type


# local constants
_KEY_RULES = _gen_cerb_rule_map()

# local globals
_invalid_type_rule = next(filter(_is_invalid_type_rule, ruleset), None)


def _get_rule_id(x: pt.ColRuleMeta) -> RuleId:
    val = x['ruleID']
    assert isinstance(val, str)
    strval = cast(str, val)
    return RuleId[strval]


def _get_dataType(x: MetaEntry) -> str:
    return x[pt.DATA_TYPE]


def _transform_rule(rule: Rule, column_meta: pt.ColMeta) -> Rule:
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
        meta = cast(Meta, column_meta[ix]['meta'])
        if pt.BOOLEAN in map(_get_dataType, meta):
            return new_rule

    return rule


def _get_allowed_values(cerb_rules: dict[str, str]) -> set[str]:
    return set(map(str, cerb_rules.get('allowed', [])))


def _get_column_rule_metas(column_meta: ColMeta) -> Meta:
    result: Meta = []
    for rule_meta in column_meta:
        result += cast(Meta, rule_meta.get('meta', []))
    return result


def _extract_datatype(column_meta: pt.ColMeta) -> Optional[str]:
    # XXX: depends on meta (which should only be for debug)
    assert column_meta is not None
    rule_metas = _get_column_rule_metas(column_meta)
    datatype_metas = filter(lambda x: pt.DATA_TYPE in x, rule_metas)
    odm_type = next(datatype_metas, {}).get(pt.DATA_TYPE)
    return odm_type


def _get_rule_for_cerb_key(key: str, column_meta: pt.ColMeta) -> Optional[Rule]:
    rule = _KEY_RULES.get(key)
    if not rule:
        logging.error(f'missing handler for cerberus rule "{key}"')
        return None
    return _transform_rule(rule, column_meta)


def _cerb_to_odm_type(cerb_type: Optional[str]) -> Optional[str]:
    t = cerb_type
    if t in {'boolean', 'datetime', 'integer', 'float'}:
        return t
    return None


def _gen_error_entry(
    vctx: ValidationCtx,
    cerb_rule: str,
    table_id: pt.TableId,
    column_id: str,
    value: SomeValue,
    row_numbers: list[int],
    rows: list[dict],
    column_meta: pt.ColMeta,
    rule_filter: RuleFilter,
    constraint: Optional[Union[str, int, float]] = None,
    schema_column: Optional[dict[str, str]] = None,
    data_kind: DataKind = DataKind.python,
) -> Optional[RuleError]:
    "Generates a single validation error from input params."
    if not value and cerb_rule == 'type':
        return None

    rule = _get_rule_for_cerb_key(cerb_rule, column_meta)
    if not (rule and rule_filter.enabled(rule)):
        return None

    # Only report column errors for the first line in spreadsheets.
    # It will always trigger on the first line do to how csv-files are
    # imported.
    if rule.is_column and data_kind == DataKind.spreadsheet:
        first_row_num = get_row_num(0, 0, data_kind)
        assert len(row_numbers) == 1
        if row_numbers[0] > first_row_num:
            return None

    cerb_type = schema_column.get('type', None) if schema_column else None
    odm_type = _extract_datatype(column_meta)
    datatype = odm_type or _cerb_to_odm_type(cerb_type)

    allowed = _get_allowed_values(schema_column) if schema_column else set()
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


def _get_cerb_rule(e: ValidationError) -> str:
    rule = e.schema_path[-1]

    # 'anyof' may be used to wrap the actual rule together with 'empty'
    if rule == 'anyof':
        (key, _) = get_anyof_constraint(e.constraint[0])
        rule = key

    return rule


def _gen_cerb_error_entry(vctx: ValidationCtx, e: ValidationError, row: dict,
                          schema: CerberusSchema, rule_filter: RuleFilter,
                          offset: int, data_kind: DataKind
                          ) -> Optional[RuleError]:
    "Transforms a single Cerberus error into a validation error."
    cerb_rule = _get_cerb_rule(e)
    (table_id, _, column_id) = e.document_path
    row_index = e.document_path[1]
    schema_column = schema[table_id]['schema']['schema'][column_id]
    column_meta: pt.ColMeta = schema_column.get('meta', [])
    row_numbers = [get_row_num(row_index, offset, data_kind)]
    rows = [row]
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


def _gen_aggregated_error_entry(vctx: ValidationCtx,
                                agg_error: AggregatedError,
                                rule_filter: RuleFilter
                                ) -> Optional[RuleError]:
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


def _get_table_name(x: dict) -> str:
    return x['tableName']


def _get_row_num(x: dict) -> Union[int, list[int]]:
    return x.get('rowNumber') or x.get('rowNumbers', [])


def _get_column_name(x: dict) -> str:
    return x['columnName']


def _get_error_rule_id(x: dict) -> RuleId:
    assert 'errorType' in x, x
    strval = x['errorType']
    return RuleId[strval]


def _get_table_rownum_column(x: dict) -> tuple[str, str, int]:
    row_num = _get_row_num(x)
    if isinstance(row_num, list):
        if len(row_num) > 0:
            row_num = row_num[0]
        else:
            row_num = 0
    assert isinstance(row_num, int)
    return (_get_table_name(x), _get_column_name(x), row_num)


def _sort_errors(errors: list[dict]) -> list[dict]:
    """Sorts errors by table, row-num, column."""
    return sorted(errors, key=_get_table_rownum_column)


def filter_errors(errors: list[dict]) -> list[dict]:
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


def map_cerb_errors(vctx: ValidationCtx, table_id: pt.TableId,
                    cerb_errors: list[ValidationError], schema: Schema,
                    rule_filter: RuleFilter, offset: int, data_kind: DataKind
                    ) -> tuple[list[dict], list[dict]]:
    """Transforms Cerberus errors to validation errors (and warnings).

    :return: a pair of lists (errors, warnings).
    """
    errors: list[dict] = []
    warnings: list[dict] = []
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


def map_aggregated_errors(vctx: ValidationCtx, table_id: pt.TableId,
                          agg_errors: list[AggregatedError],
                          rule_filter: RuleFilter) -> list[dict]:
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


def gen_additions_schema(additions: dict) -> CerberusSchema:
    # This may work for all rules, but 'allowed' is the only officially
    # supported one.
    result: CerberusSchema = {}
    for table_id, attributes in additions.items():
        attr_schema = attributes
        table_schema = init_table_schema(table_id, [], attr_schema)
        deep_update(result, table_schema)
    return result
