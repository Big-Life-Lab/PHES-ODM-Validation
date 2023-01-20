"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

import os
import re
import sys
from dataclasses import dataclass
from itertools import groupby
from os.path import join, normpath
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
# from pprint import pprint

from cerberusext import OdmValidator

import part_tables as pt
import rules
from rules import Rule, ruleset
from schemas import Schema
from stdext import (
    deep_update,
    deduplicate_dict_list,
    flatten,
    get_len,
    type_name,
)
from versions import __version__, parse_version


@dataclass
class ErrorContext:
    allowed_values: Set[str]
    column_id: str
    constraint: Any
    odm_datatype: str
    row: dict
    row_num: int
    rule: Rule
    rule_fields: list
    table_id: str
    value: Any


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


# public constants
ODM_LATEST = _get_latest_odm_version()

# private constants
_KEY_RULES = {r.key: r for r in ruleset}


def _prettify_rule_name(rule: Rule):
    return rule.id.replace('_', ' ').capitalize()


def _fmt_allowed_values(values: Set[str]) -> str:
    # XXX: The order of set-elements isn't deterministic, so we need to sort.
    return '/'.join(sorted(values))


def _error_msg(ctx: ErrorContext):
    error_template = ctx.rule.get_error_template(ctx.value, ctx.odm_datatype)
    return error_template.format(
        allowed_values=_fmt_allowed_values(ctx.allowed_values),
        rule_name=_prettify_rule_name(ctx.rule),
        table_id=ctx.table_id,
        column_id=ctx.column_id,
        row_num=ctx.row_num,
        value=ctx.value,
        value_len=get_len(ctx.value),
        value_type=type_name(type(ctx.value)),
        constraint=ctx.constraint,
    )


def _gen_rule_error(ctx: ErrorContext):
    error = {
        'errorType': ctx.rule.id,
        'tableName': ctx.table_id,
        'columnName': ctx.column_id,
        'rowNumber': ctx.row_num,
        'row': ctx.row,
        'validationRuleFields': ctx.rule_fields,
        'message': _error_msg(ctx),
    }
    if ctx.value:
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
    if rule.key == 'allowed':
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


def _gen_error_entry(e, row, schema: Schema, rule_whitelist: List[str]
                     ) -> Optional[dict]:
    rule_key = e.schema_path[-1]
    (table_id, row_index, column_id) = e.document_path
    column = schema['schema'][table_id]['schema']['schema'][column_id]
    column_meta = column.get('meta', [])
    rule = _get_rule_for_cerb_key(rule_key, column_meta)

    if len(rule_whitelist) > 0 and rule.id not in rule_whitelist:
        return

    # XXX: depends on meta (which should only be for debug)
    odm_datatype = _extract_datatype(column_meta)

    rule_fields = pt.get_validation_rule_fields(column_meta, [rule.id])
    error_ctx = ErrorContext(rule=rule, table_id=table_id, column_id=column_id,
                             row_num=row_index+1, row=row, value=e.value,
                             constraint=e.constraint, rule_fields=rule_fields,
                             allowed_values=_get_allowed_values(column),
                             odm_datatype=odm_datatype)
    return _gen_rule_error(error_ctx)


def _generate_validation_schema_ext(parts, schema_version,
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
        deep_update(s, cerb_schema)

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


def generate_validation_schema(parts, schema_version=ODM_LATEST) -> Schema:
    return _generate_validation_schema_ext(parts, schema_version)


def _validate_data_ext(schema: Schema,
                       data: dict,
                       data_version: str = ODM_LATEST,
                       rule_whitelist: List[str] = [],
                       ) -> ValidationReport:
    """Validates `data` with `schema`, using Cerberus."""
    # `rule_whitelist` determines which rules/errors are triggered during
    # validation. It is needed when testing data validation, to be able to
    # compare error reports in isolation.
    errors = []
    warnings = []
    coercion_warnings = []
    coercion_errors = []
    cerb_schema = schema["schema"]
    v = OdmValidator(coercion_warnings=coercion_warnings,
                     coercion_errors=coercion_errors)
    assert isinstance(cerb_schema, dict)
    if not v.validate(data, cerb_schema):
        for table_error in v._errors:
            for row_errors in table_error.info:
                for e in row_errors:
                    row = e.value
                    for attr_errors in e.info:
                        for e in attr_errors:
                            entry = _gen_error_entry(e, row, schema,
                                                     rule_whitelist)
                            if entry:
                                errors.append(entry)
    errors += coercion_errors
    warnings += coercion_warnings

    return ValidationReport(
        data_version=data_version,
        schema_version=schema["schemaVersion"],
        package_version=__version__,
        errors=errors,
        warnings=warnings,
    )


def validate_data(schema: Schema,
                  data: dict,
                  data_version=ODM_LATEST,
                  ) -> ValidationReport:
    return _validate_data_ext(schema, data, data_version)
