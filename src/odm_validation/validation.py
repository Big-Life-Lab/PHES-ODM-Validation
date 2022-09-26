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
from typing import List

from cerberus import Validator

import utils
import part_tables as pt
from rules import ruleset
from schemas import Schema
from versions import __version__, parse_version


@dataclass(frozen=True)
class ValidationReport:
    data_version: str
    schema_version: str
    package_version: str
    errors: List[str]

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
        v = parse_version(match.group(1))
        versions.append(str(v))
    if len(versions) == 0:
        sys.exit("failed to get latest ODM version")
    versions.sort()
    return versions[-1]


# public globals
ODM_LATEST = _get_latest_odm_version()

# private globals
_KEY_RULES = {r.key: r for r in ruleset}


def _rule_name(rule_id):
    return rule_id.replace('_', ' ').capitalize()


def _error_msg(rule, table_id, column_id, row_num, value):
    return rule.error_template.format(
        rule_name=_rule_name(rule.id),
        table_id=table_id,
        column_id=column_id,
        row_num=row_num,
        value=value,
    )


def _gen_rule_error(rule, table, column, row_index, row, value):
    row_num = row_index + 1
    error = {
        'errorType': rule.id,
        'tableName': table,
        'columnName': column,
        'rowNumber': row_num,
        'row': row,
        'message': _error_msg(rule, table, column, row_num, value),
        'invalidValue': value,
    }
    return error


def _gen_error_entry(e, row) -> str:
    rule_key = e.schema_path[-1]
    rule = _KEY_RULES.get(rule_key)
    assert rule, f'missing rule for constraint "{rule_key}"'
    (table, row_index, column) = e.document_path
    return _gen_rule_error(rule, table, column, row_index, row, e.value)


def generate_validation_schema(parts, odm_version=ODM_LATEST) -> Schema:
    cerb_schema = {}
    data = pt.gen_partdata(parts, odm_version)
    for r in ruleset:
        s = r.gen_schema(data)
        assert s is not None
        utils.deep_update(s, cerb_schema)
    return {
        "schemaVersion": odm_version,
        "schema": cerb_schema,
    }


def validate_data(schema: Schema,
                  data: dict,
                  data_version=ODM_LATEST
                  ) -> ValidationReport:
    """Validates `data` with `schema`, using Cerberus."""
    # Unknown fields must be allowed because we're only generating a schema
    # for the requirements, not the optional data.
    v = Validator(schema["schema"])
    v.allow_unknown = True

    errors = []
    if not v.validate(data):
        for table_error in v._errors:
            for row_errors in table_error.info:
                for e in row_errors:
                    row = e.value
                    for attr_errors in e.info:
                        for e in attr_errors:
                            errors.append(_gen_error_entry(e, row))

    return ValidationReport(
        data_version=data_version,
        schema_version=schema["schemaVersion"],
        package_version=__version__,
        errors=errors,
    )
