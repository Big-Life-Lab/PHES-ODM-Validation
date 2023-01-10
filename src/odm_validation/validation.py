"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

import os
import re
import sys
from dataclasses import dataclass
from os.path import join, normpath
from pathlib import Path
from typing import Any, List, Optional
# from pprint import pprint

from cerberusext import OdmValidator

import part_tables as pt
from rules import Rule, ruleset
from schemas import Schema
from stdext import deep_update, deduplicate_dict_list
from versions import __version__, parse_version


@dataclass
class ErrorContext:
    column_id: str
    constraint: Any
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


# public globals
ODM_LATEST = _get_latest_odm_version()

# private globals
_KEY_RULES = {r.key: r for r in ruleset}


def _prettify_rule_name(rule: Rule):
    return rule.id.replace('_', ' ').capitalize()


def _error_msg(ctx: ErrorContext):
    return ctx.rule.error_template.format(
        rule_name=_prettify_rule_name(ctx.rule),
        table_id=ctx.table_id,
        column_id=ctx.column_id,
        row_num=ctx.row_num,
        value=ctx.value,
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


def _gen_error_entry(e, row, schema: Schema) -> Optional[dict]:
    # We are currently using the 'type' rule without having a rule-handler for
    # it. This means that we'll get a type error from Cerberus if something
    # wasn't coerced properly, which in turn causes an invalid validation
    # result. The current workaround for this is to check for the type error
    # and ignore it.
    rule_key = e.schema_path[-1]
    rule = _KEY_RULES.get(rule_key)
    if not rule and rule_key == 'type':
        return
    assert rule, f'missing handler for cerberus rule "{rule_key}"'
    (table_id, row_index, column_id) = e.document_path
    column = schema['schema'][table_id]['schema']['schema'][column_id]
    column_meta = column.get('meta', [])
    rule_fields = pt.get_validation_rule_fields(column_meta, [rule.id])
    error_ctx = ErrorContext(rule=rule, table_id=table_id, column_id=column_id,
                             row_num=row_index+1, row=row, value=e.value,
                             constraint=e.constraint, rule_fields=rule_fields)
    return _gen_rule_error(error_ctx)


def generate_validation_schema(parts, schema_version=ODM_LATEST) -> Schema:
    # `parts` must be stripped before further processing. This is important for
    # performance and simplicity of implementation.
    version = parse_version(schema_version)
    parts = pt.strip(parts)
    parts = pt.filter_compatible(parts, version)
    data = pt.gen_partdata(parts, version)

    cerb_schema = {}
    for r in ruleset:
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


def validate_data(schema: Schema,
                  data: dict,
                  data_version=ODM_LATEST,
                  ) -> ValidationReport:
    """Validates `data` with `schema`, using Cerberus."""
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
                            entry = _gen_error_entry(e, row, schema)
                            if not entry:
                                continue
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
