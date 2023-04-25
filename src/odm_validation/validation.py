"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

from collections import defaultdict
from collections.abc import Iterable, Iterator
from copy import deepcopy
from itertools import groupby
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
# from pprint import pprint

from cerberusext import ContextualCoercer, OdmValidator

import part_tables as pt
import reports
from input_data import DataKind
from reports import ErrorKind, get_row_num
from rules import Rule, RuleId, ruleset
from schemas import CerberusSchema, Schema, init_table_schema
from stdext import (
    countdown,
    deep_update,
    flatten,
    strip_dict_key,
)
from versions import __version__, parse_version


RuleError = Tuple[RuleId, dict]
TableDataset = Dict[pt.TableId, pt.Dataset]


class RuleFilter:
    """A rule filter.

    The blacklist takes precedence over the whitelist, and an empty whitelist
    represents all rules."""
    # `whitelist` is needed when testing schema generation and data validation.
    # Users may be more interested in `blacklist`, to remove certain irrelevant
    # errors from their reports.

    blacklist: List[RuleId]
    whitelist: List[RuleId]

    def __init__(self, blacklist=[], whitelist=[]):
        self.blacklist = blacklist
        self.whitelist = whitelist

    def enabled(self, rule: Rule):
        "Returns true if the rule `rule_id` is enabled."
        rule_id = rule.id
        return (rule_id not in self.blacklist and
                (rule_id in self.whitelist or self.whitelist == []))

    def filter(self, rules: Iterable[Rule]) -> Iterator[Rule]:
        return filter(self.enabled, rules)


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


# private constants
_BATCH_SIZE = 100
_KEY_RULES = _gen_cerb_rule_map()


def _get_rule_id(x):
    return x['ruleID']


def _get_dataType(x):
    return x[pt.DATA_TYPE]


def _is_invalid_type_rule(rule):
    return rule.id == RuleId.invalid_type


def _transform_rule(rule: Rule, column_meta) -> Rule:
    """Returns a new rule, depending on `column_meta`. Currently only returns
    invalid_type if rule-key is 'allowed' and dataType is bool."""
    # XXX: dependency on meta value (which is only supposed to aid debug)
    # XXX: does not handle rules with match_all_keys enabled
    if rule.keys[0] == 'allowed':
        rule_ids = list(map(_get_rule_id, column_meta))
        new_rule = next(filter(_is_invalid_type_rule, ruleset), None)
        new_rule_id = new_rule.id.name
        if not new_rule or (new_rule_id not in rule_ids):
            return rule
        ix = rule_ids.index(new_rule_id)
        if pt.BOOLEAN in map(_get_dataType, column_meta[ix]['meta']):
            return new_rule
    return rule


def _get_allowed_values(cerb_rules: Dict[str, Any]) -> Set[str]:
    return set(cerb_rules.get('allowed', []))


def _extract_datatype(column_meta: list) -> Optional[str]:
    # XXX: depends on meta (which should only be for debug)
    rule_metas = flatten(map(lambda x: x['meta'], column_meta))
    datatype_metas = filter(lambda x: pt.DATA_TYPE in x, rule_metas)
    odm_type = next(datatype_metas, {}).get(pt.DATA_TYPE)
    return odm_type


def _get_rule_for_cerb_key(key: str, column_meta) -> Rule:
    rule = _KEY_RULES.get(key)
    assert rule, f'missing handler for cerberus rule "{key}"'
    return _transform_rule(rule, column_meta)


def _cerb_to_odm_type(cerb_type: str) -> Optional[str]:
    t = cerb_type
    if t in {'boolean', 'datetime', 'integer', 'float'}:
        return t


def _gen_error_entry(cerb_rule, table_id, column_id, value, row_numbers,
                     rows, column_meta, rule_filter: RuleFilter,
                     constraint=None, schema_column=None,
                     data_kind=DataKind.python
                     ) -> Optional[RuleError]:
    "Generates a single validation error from input params."
    if not value and cerb_rule == 'type':
        return

    rule = _get_rule_for_cerb_key(cerb_rule, column_meta)
    if not rule_filter.enabled(rule):
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
    )
    entry = reports.gen_rule_error(error_ctx, kind=kind)
    return (rule.id, entry)


def _gen_cerb_error_entry(e, row, schema: CerberusSchema,
                          rule_filter: RuleFilter, offset: int,
                          data_kind: DataKind) -> Optional[RuleError]:
    "Transforms a single Cerberus error into a validation error."
    cerb_rule = e.schema_path[-1]
    (table_id, _, column_id) = e.document_path
    row_index = e.document_path[1]
    schema_column = schema[table_id]['schema']['schema'][column_id]
    column_meta = schema_column.get('meta', [])
    row_numbers = [get_row_num(row_index, offset, data_kind)]
    rows = [row]
    return _gen_error_entry(
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


def _gen_aggregated_error_entry(agg_error, rule_filter: RuleFilter
                                ) -> Optional[dict]:
    """Transforms a single aggregated error (from OdmValidator) to a validation
    error."""
    return _gen_error_entry(
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


def _get_error_rule_id(x):
    assert 'errorType' in x, x
    return x['errorType']


def _get_table_rownum_column(x):
    row_num = _get_row_num(x)
    if row_num is not None and isinstance(row_num, list):
        row_num = row_num[0]
    return (_get_table_name(x), _get_column_name(x), row_num)


def _sort_errors(errors):
    """Sorts errors by table, row-num, column."""
    return sorted(errors, key=_get_table_rownum_column)


def _filter_errors(errors):
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
                if RuleId.invalid_type.name in rule_ids:
                    for i in countdown(len(value_errors)):
                        if rule_ids[i] == RuleId._coercion.name:
                            del value_errors[i]
                result += value_errors
    return result


def _strip_coerce_rules(cerb_schema):
    return strip_dict_key(deepcopy(cerb_schema), 'coerce')


def _map_cerb_errors(table_id, cerb_errors, schema, rule_filter,
                     summary: reports.ValidationSummary, offset: int,
                     data_kind):
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
                        rule_error = _gen_cerb_error_entry(e, row, schema,
                                                           rule_filter, offset,
                                                           data_kind)
                        if not rule_error:
                            continue
                        (rule_id, entry) = rule_error
                        summary.record_error(table_id, rule_id)
                        if 'warningType' in entry:
                            warnings.append(entry)
                        else:
                            errors.append(entry)
    return errors, warnings


def _map_aggregated_errors(table_id, agg_errors, rule_filter, summary):
    """Transforms a list of aggregated errors from OdmValidator to a list of
    validation errors."""
    errors = []
    for ae in agg_errors:
        rule_error = _gen_aggregated_error_entry(ae, rule_filter)
        if not rule_error:
            continue
        (rule_id, entry) = rule_error
        summary.record_error(table_id, rule_id)
        errors.append(entry)
    return errors


def _gen_additions_schema(additions) -> CerberusSchema:
    # This may work for all rules, but 'allowed' is the only officially
    # supported one.
    result = {}
    for table_id, attributes in additions.items():
        attr_schema = attributes
        table_schema = init_table_schema(table_id, [], attr_schema)
        deep_update(result, table_schema)
    return result


def _generate_validation_schema_ext(parts: pt.Dataset,
                                    sets: pt.Dataset = [],
                                    schema_version: str = pt.ODM_VERSION_STR,
                                    schema_additions: dict = {},
                                    rule_blacklist: List[RuleId] = [],
                                    rule_whitelist: List[RuleId] = []
                                    ) -> Schema:
    """
    This is the extended version of `generate_validation_schema`, with
    additional parameters for setting advanced options.

    :param rule_whitelist: A list of rule ids to explicitly enable. An empty
        list represents all the rules.
    :param rule_blacklist: A list of rule ids to explicitly disable. This takes
        precedence over the whitelist.
    """
    # `parts` must be stripped before further processing. This is important for
    # performance and simplicity of implementation.
    # `rule_whitelist` determines which rules are included in the schema. It is
    # needed when testing schema generation, to be able to compare isolated
    # rule-specific schemas.
    assert isinstance(sets, list), "invalid sets param"
    version = parse_version(schema_version)
    odm_data = pt.gen_odmdata(parts, sets, version)

    rule_filter = RuleFilter(whitelist=rule_whitelist,
                             blacklist=rule_blacklist)
    enabled_rules = list(rule_filter.filter(ruleset))

    cerb_schema = {}
    for r in enabled_rules:
        assert r.gen_schema, f'missing `gen_schema` in rule {r.id}'
        s = r.gen_schema(odm_data, version)
        assert s is not None
        deep_update(cerb_schema, s)
    additions_schema = _gen_additions_schema(schema_additions)
    deep_update(cerb_schema, additions_schema)

    # strip empty tables
    for table in list(cerb_schema):
        if cerb_schema[table]['schema']['schema'] == {}:
            del cerb_schema[table]

    return {
        "schemaVersion": schema_version,
        "schema": cerb_schema,
    }


def generate_validation_schema(parts: pt.Dataset,
                               sets: pt.Dataset = [],
                               schema_version=pt.ODM_VERSION_STR,
                               schema_additions={}) -> Schema:
    return _generate_validation_schema_ext(parts, sets, schema_version,
                                           schema_additions)


# OnProgress(action, table_id, processed, total)
OnProgress = Callable[[str, str, int, int], None]


def _validate_data_ext(schema: Schema,
                       data: TableDataset,
                       data_kind: DataKind = DataKind.python,
                       data_version: str = pt.ODM_VERSION_STR,
                       rule_blacklist: List[RuleId] = [],
                       rule_whitelist: List[RuleId] = [],
                       on_progress: OnProgress = None,
                       batch_size=_BATCH_SIZE,
                       ) -> reports.ValidationReport:
    """
    Validates `data` with `schema`, using Cerberus.

    This is the extended version of `validate_data`, with additional parameters
    for setting advanced options.

    :param rule_whitelist: list of rule ids to explicitly enable.
    :param rule_blacklist: list of rule ids to explicitly disable.
    """
    # `rule_whitelist` determines which rules/errors are triggered during
    # validation. It is needed when testing data validation, to be able to
    # compare error reports in isolation.
    #
    # The schema is being put through two steps. First, coercion is done by
    # looking at the `coerce` rules, then those rules are stripped and
    # validation is performed on the remaining rules.

    # inform user of param order/type mistakes
    assert isinstance(data, dict), (
        '`data` must be a dict. Remember to wrap the datasets in a dict with '
        'the table names as keys.')
    assert isinstance(data_kind, DataKind), 'invalid data_kind param type'
    assert isinstance(data_version, str), 'invalid data_version param type'
    assert isinstance(rule_whitelist, list), \
        'invalid rule_whitelist param type'

    errors = []
    warnings = []
    versioned_schema = schema
    cerb_schema = versioned_schema["schema"]
    coercion_schema = cerb_schema
    summary = reports.ValidationSummary()
    rule_filter = RuleFilter(whitelist=rule_whitelist,
                             blacklist=rule_blacklist)

    def batch_table_data(action, table_id, table_data):
        total = len(table_data)
        offset = 0
        while offset < total:
            n = min(total - offset, batch_size)
            first = offset
            last = offset + n
            batch_data = {table_id: table_data[first:last]}
            yield (batch_data, offset)
            offset += n
            if on_progress:
                on_progress(action, table_id, offset, total)

    coerced_data = defaultdict(list)
    coercer = ContextualCoercer(warnings=warnings, errors=errors)
    for table_id, table_data in data.items():
        for batch in batch_table_data('coercing', table_id, table_data):
            batch_data, offset = batch
            coerce_result = coercer.coerce(batch_data, coercion_schema,
                                           offset, data_kind)
            coerced_data[table_id] += coerce_result[table_id]

    validation_schema = _strip_coerce_rules(coercion_schema)
    for table_id, table_data in coerced_data.items():
        v = OdmValidator.new()
        for batch in batch_table_data('validating', table_id, table_data):
            batch_data, offset = batch
            v._errors.clear()
            if v.validate(offset, data_kind, batch_data, validation_schema):
                continue
            e, w = _map_cerb_errors(table_id, v._errors, validation_schema,
                                    rule_filter, summary, offset, data_kind)
            errors += e
            warnings += w
        errors += _map_aggregated_errors(table_id,
                                         v.error_state.aggregated_errors,
                                         rule_filter, summary)

    errors = _filter_errors(errors)

    return reports.ValidationReport(
        data_version=data_version,
        schema_version=versioned_schema["schemaVersion"],
        package_version=__version__,
        errors=errors,
        warnings=warnings,
        summary=summary,
    )


def validate_data(schema: Schema,
                  data: TableDataset,
                  data_kind: DataKind = DataKind.python,
                  data_version=pt.ODM_VERSION_STR,
                  rule_blacklist: List[RuleId] = [],
                  ) -> reports.ValidationReport:
    """
    :param rule_blacklist: A list of rule ids to explicitly disable.
    """
    return _validate_data_ext(schema, data, data_kind, data_version,
                              rule_blacklist)
