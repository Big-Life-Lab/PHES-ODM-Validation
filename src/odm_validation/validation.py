"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

import os
import re
import sys
from copy import deepcopy
from dataclasses import dataclass
from itertools import groupby
from os.path import join, normpath
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
# from pprint import pprint

from cerberusext import ContextualCoercer, OdmValidator

import part_tables as pt
import rules
from rules import Rule, ruleset
from schemas import CerberusSchema, Schema, init_table_schema
from stdext import (
    deduplicate_dict_list,
    deep_update,
    flatten,
    get_len,
    strip_dict_key,
    type_name,
)
from versions import __version__, parse_version


@dataclass(frozen=True)
class ErrorContext:
    allowed_values: Set[str]
    column_id: str
    constraint: Any
    odm_datatype: str
    rows: List[dict]
    row_numbers: List[int]
    rule: Rule
    rule_fields: list
    table_id: str
    value: Any
    is_warning: bool


@dataclass(frozen=True)
class ValidationReport:
    data_version: str
    schema_version: str
    package_version: str
    errors: List[str]
    warnings: List[str]

    def valid(self) -> bool:
        return len(self.errors) == 0


def _get_latest_odm_version() -> str:
    file_path = normpath(os.path.realpath(__file__))
    root_dir = join(os.path.dirname(file_path), '../..')
    dict_dir = join(root_dir, 'assets/dictionary')
    versions = []
    for dir_path in Path(dict_dir).glob('v*'):
        dir_name = os.path.basename(dir_path)
        if not (match := re.search('v(.+)', dir_name)):
            continue
        v = parse_version(match.group(1), verbose=False)
        versions.append(str(v))
    if len(versions) == 0:
        sys.exit("failed to get latest ODM version")
    versions.sort()
    return versions[-1]


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


# public constants
ODM_LATEST = _get_latest_odm_version()

# private constants
_KEY_RULES = _gen_cerb_rule_map()


def _prettify_rule_name(rule: Rule):
    return rule.id.replace('_', ' ').capitalize()


def _fmt_allowed_values(values: Set[str]) -> str:
    # XXX: The order of set-elements isn't deterministic, so we need to sort.
    return '/'.join(sorted(values))


def _fmt_list(items: list) -> str:
    if len(items) > 1:
        return ','.join(map(str, items))
    else:
        return str(items[0])


def _error_msg(ctx: ErrorContext):
    error_template = ctx.rule.get_error_template(ctx.value, ctx.odm_datatype)
    return error_template.format(
        allowed_values=_fmt_allowed_values(ctx.allowed_values),
        rule_name=_prettify_rule_name(ctx.rule),
        table_id=ctx.table_id,
        column_id=ctx.column_id,
        row_num=_fmt_list(ctx.row_numbers),
        value=ctx.value,
        value_len=get_len(ctx.value),
        value_type=type_name(type(ctx.value)),
        constraint=ctx.constraint,
    )


def _gen_rule_error(ctx: ErrorContext):
    error = {
        'tableName': ctx.table_id,
        'columnName': ctx.column_id,
        'validationRuleFields': ctx.rule_fields,
        'message': _error_msg(ctx),
    }

    # type
    if ctx.is_warning:
        error['warningType'] = ctx.rule.id
    else:
        error['errorType'] = ctx.rule.id

    # row numbers
    if len(ctx.row_numbers) > 1:
        error['rowNumbers'] = ctx.row_numbers
    else:
        error['rowNumber'] = ctx.row_numbers[0]

    # rows
    if len(ctx.rows) > 1:
        error['rows'] = ctx.rows
    else:
        error['row'] = ctx.rows[0]

    # value
    if ctx.value is not None:
        error['invalidValue'] = ctx.value

    return error


def _get_ruleId(x):
    return x['ruleID']


def _get_dataType(x):
    return x[pt.DATA_TYPE]


def _is_invalid_type_rule(rule):
    return rule.id == rules.invalid_type.__name__


def _transform_rule(rule: Rule, column_meta) -> Rule:
    """Returns a new rule, depending on `column_meta`. Currently only returns
    invalid_type if rule-key is 'allowed' and dataType is bool."""
    # XXX: dependency on meta value (which is only supposed to aid debug)
    # XXX: does not handle rules with match_all_keys enabled
    if rule.keys[0] == 'allowed':
        rule_ids = list(map(_get_ruleId, column_meta))
        new_rule = next(filter(_is_invalid_type_rule, ruleset), None)
        if not new_rule or new_rule.id not in rule_ids:
            return rule
        ix = rule_ids.index(new_rule.id)
        if pt.BOOLEAN in map(_get_dataType, column_meta[ix]['meta']):
            return new_rule
    return rule


def _get_allowed_values(cerb_rules: Dict[str, Any]) -> Set[str]:
    return set(cerb_rules.get('allowed', []))


def _extract_datatype(column_meta: list) -> Optional[str]:
    rule_metas = flatten(map(lambda x: x['meta'], column_meta))
    datatype_metas = filter(lambda x: pt.DATA_TYPE in x, rule_metas)
    return next(datatype_metas, {}).get(pt.DATA_TYPE)


def _get_rule_for_cerb_key(key: str, column_meta) -> Rule:
    rule = _KEY_RULES.get(key)
    assert rule, f'missing handler for cerberus rule "{key}"'
    return _transform_rule(rule, column_meta)


def _gen_error_entry(cerb_rule, table_id, column_id, value, row_numbers,
                     rows, column_meta, rule_whitelist: List[str],
                     constraint=None, schema_column=None,
                     ) -> Optional[dict]:
    rule = _get_rule_for_cerb_key(cerb_rule, column_meta)
    if len(rule_whitelist) > 0 and rule.id not in rule_whitelist:
        return

    # XXX: depends on meta (which should only be for debug)
    odm_datatype = _extract_datatype(column_meta)

    rule_fields = pt.get_validation_rule_fields(column_meta, [rule.id])
    allowed = _get_allowed_values(schema_column) if schema_column else []
    error_ctx = ErrorContext(rule=rule, table_id=table_id, column_id=column_id,
                             row_numbers=row_numbers, rows=rows, value=value,
                             constraint=constraint, rule_fields=rule_fields,
                             allowed_values=allowed,
                             odm_datatype=odm_datatype,
                             is_warning=rule.is_warning)
    return _gen_rule_error(error_ctx)


def _gen_cerb_error_entry(e, row, schema: CerberusSchema,
                          rule_whitelist: List[str]) -> Optional[dict]:
    cerb_rule = e.schema_path[-1]
    (table_id, row_index, column_id) = e.document_path
    schema_column = schema[table_id]['schema']['schema'][column_id]
    column_meta = schema_column.get('meta', [])
    row_numbers = [row_index + 1]
    rows = [row]
    return _gen_error_entry(
        cerb_rule,
        table_id,
        column_id,
        e.value,
        row_numbers,
        rows,
        column_meta,
        rule_whitelist,
        e.constraint,
        schema_column
    )


def _gen_aggregated_error_entry(agg_error,
                                rule_whitelist: List[str]
                                ) -> Optional[dict]:
    return _gen_error_entry(
        agg_error.cerb_rule,
        agg_error.table_id,
        agg_error.column_id,
        agg_error.value,
        agg_error.row_numbers,
        agg_error.rows,
        agg_error.column_meta,
        rule_whitelist
    )


def _get_table_name(x):
    return x['tableName']


def _get_row_num(x):
    return x.get('rowNumber') or x.get('rowNumbers')


def _get_column_name(x):
    return x['columnName']


def _get_rule_id(x):
    assert 'errorType' in x, x
    return x['errorType']


def _get_table_rownum_column(x):
    return (_get_table_name(x), _get_row_num(x), _get_column_name(x))


def _sort_errors(errors):
    """Sorts errors by table, row-num, column."""
    return sorted(errors, key=_get_table_rownum_column)


def _filter_errors(errors):
    """Removes redundant errors."""
    # - invalid_type produces redundant _coercion errors
    result = []
    target_rule_ids = {rules._COERCION}
    sorted_errors = _sort_errors(errors)
    for tableName, table_errors in groupby(sorted_errors, _get_table_name):
        for rowNum, row_errors in groupby(table_errors, _get_row_num):
            for columnName, col_errors in groupby(row_errors,
                                                  _get_column_name):
                value_errors = list(col_errors)
                rule_ids = list(map(_get_rule_id, value_errors))
                if rules.invalid_type.__name__ in rule_ids:
                    for id in set(rule_ids).intersection(target_rule_ids):
                        ix = rule_ids.index(id)
                        del value_errors[ix]
                result += value_errors
    return result


def _coerce_data(data, schema, warnings, errors):
    coercer = ContextualCoercer(warnings=warnings, errors=errors)
    return coercer.coerce(data, schema)


def _strip_coerce_rules(cerb_schema):
    return strip_dict_key(deepcopy(cerb_schema), 'coerce')


def _map_errors(cerb_errors, schema, rule_whitelist):
    errors = []
    warnings = []
    for table_error in cerb_errors:
        for row_errors in table_error.info:
            for e in row_errors:
                row = e.value
                for attr_errors in e.info:
                    for e in attr_errors:
                        entry = _gen_cerb_error_entry(e, row, schema,
                                                      rule_whitelist)
                        if not entry:
                            continue
                        if 'warningType' in entry:
                            warnings.append(entry)
                        else:
                            errors.append(entry)
    return errors, warnings


def _map_aggregated_errors(agg_errors, rule_whitelist):
    errors = []
    for ae in agg_errors:
        entry = _gen_aggregated_error_entry(ae, rule_whitelist)
        if entry:
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


def _generate_validation_schema_ext(parts, schema_version,
                                    schema_additions={},
                                    rule_whitelist=[]
                                    ) -> Schema:
    # `parts` must be stripped before further processing. This is important for
    # performance and simplicity of implementation.
    # `rule_whitelist` determines which rules are included in the schema. It is
    # needed when testing schema generation, to be able to compare isolated
    # rule-specific schemas.
    version = parse_version(schema_version)
    parts = pt.strip(parts)
    parts = pt.filter_compatible(parts, version)
    data = pt.gen_partdata(parts, version)

    active_rules = ruleset
    if len(rule_whitelist) > 0:
        active_rules = filter(lambda r: r.id in rule_whitelist, active_rules)

    cerb_schema = {}
    for r in active_rules:
        assert r.gen_schema, f'missing `gen_schema` in rule {r.id}'
        s = r.gen_schema(data, version)
        assert s is not None
        deep_update(cerb_schema, s)
    additions_schema = _gen_additions_schema(schema_additions)
    deep_update(cerb_schema, additions_schema)

    # `deep_update` is used to join all the table-schemas together,
    # however it will cause duplicates in the meta list. This is especially a
    # problem for the table-meta, so we'll need to deduplicate it here.
    for table in list(cerb_schema):
        table_schema = cerb_schema[table]['schema']
        if table_schema['schema'] == {}:
            del cerb_schema[table]
            continue
        table_schema['meta'] = deduplicate_dict_list(table_schema['meta'])

    return {
        "schemaVersion": schema_version,
        "schema": cerb_schema,
    }


def generate_validation_schema(parts, schema_version=ODM_LATEST,
                               schema_additions={}) -> Schema:
    return _generate_validation_schema_ext(parts, schema_version,
                                           schema_additions)


def _validate_data_ext(schema: Schema,
                       data: dict,
                       data_version: str = ODM_LATEST,
                       rule_whitelist: List[str] = [],
                       ) -> ValidationReport:
    """Validates `data` with `schema`, using Cerberus."""
    # `rule_whitelist` determines which rules/errors are triggered during
    # validation. It is needed when testing data validation, to be able to
    # compare error reports in isolation.
    #
    # The schema is being put through two steps. First, coercion is done by
    # looking at the `coerce` rules, then those rules are stripped and
    # validation is performed on the remaining rules.

    errors = []
    warnings = []
    versioned_schema = schema
    cerb_schema = versioned_schema["schema"]
    coercion_schema = cerb_schema

    coerced_data = _coerce_data(data, coercion_schema, warnings, errors)

    v = OdmValidator.new()
    validation_schema = _strip_coerce_rules(coercion_schema)
    if not v.validate(coerced_data, validation_schema):
        e, w = _map_errors(v._errors, validation_schema, rule_whitelist)
        warnings += w
        errors += e
        errors += _map_aggregated_errors(v.error_state.aggregated_errors,
                                         rule_whitelist)

    errors = _filter_errors(errors)

    return ValidationReport(
        data_version=data_version,
        schema_version=versioned_schema["schemaVersion"],
        package_version=__version__,
        errors=errors,
        warnings=warnings,
    )


def validate_data(schema: Schema,
                  data: dict,
                  data_version=ODM_LATEST,
                  ) -> ValidationReport:
    return _validate_data_ext(schema, data, data_version)
