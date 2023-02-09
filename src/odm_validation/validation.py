"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

from copy import deepcopy
from itertools import groupby
from typing import Any, Dict, List, Optional, Set
# from pprint import pprint

from cerberusext import ContextualCoercer, OdmValidator

import part_tables as pt
import reports
import rules
from reports import ErrorKind
from rules import Rule, ruleset
from schemas import CerberusSchema, Schema, init_table_schema
from stdext import (
    deep_update,
    flatten,
    strip_dict_key,
)
from versions import __version__, parse_version


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
_KEY_RULES = _gen_cerb_rule_map()


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

    # rule_fields = pt.get_validation_rule_fields(column_meta, [rule.id])
    allowed = _get_allowed_values(schema_column) if schema_column else []
    kind = ErrorKind.WARNING if rule.is_warning else ErrorKind.ERROR
    error_ctx = reports.ErrorCtx(
        allowed_values=allowed,
        column_id=column_id,
        column_meta=column_meta,
        constraint=constraint,
        err_template=rule.get_error_template(value, odm_datatype),
        row_numbers=row_numbers,
        rows=rows, value=value,
        rule_id=rule.id,
        table_id=table_id,
    )
    return reports.gen_rule_error(error_ctx, kind=kind)


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
    target_rule_ids = {rules.COERCION_RULE_ID}
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

    # strip empty tables
    for table in list(cerb_schema):
        if cerb_schema[table]['schema']['schema'] == {}:
            del cerb_schema[table]

    return {
        "schemaVersion": schema_version,
        "schema": cerb_schema,
    }


def generate_validation_schema(parts, schema_version=pt.ODM_VERSION_STR,
                               schema_additions={}) -> Schema:
    return _generate_validation_schema_ext(parts, schema_version,
                                           schema_additions)


def _validate_data_ext(schema: Schema,
                       data: dict,
                       data_version: str = pt.ODM_VERSION_STR,
                       rule_whitelist: List[str] = [],
                       ) -> reports.ValidationReport:
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

    return reports.ValidationReport(
        data_version=data_version,
        schema_version=versioned_schema["schemaVersion"],
        package_version=__version__,
        errors=errors,
        warnings=warnings,
    )


def validate_data(schema: Schema,
                  data: dict,
                  data_version=pt.ODM_VERSION_STR,
                  ) -> reports.ValidationReport:
    return _validate_data_ext(schema, data, data_version)
