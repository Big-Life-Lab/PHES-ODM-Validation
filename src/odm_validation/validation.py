"""
This is the main module of the package. It contains functions for schema
generation and data validation.
"""

from typing import List, Optional

from cerberus import Validator

import utils
import part_tables as pt
from rules import ruleset


# types
ErrorList = List[str]


# globals
_KEY_RULES = {r.key: r for r in ruleset}


def _error_msg(rule, table, column, row_num):
    return f"{rule} in {table}.{column} in row number {row_num}."


def _gen_rule_error(rule, table, column, row_index, row, extra):
    row_num = row_index + 1
    error = {
        "errorType": rule,
        "tableName": table,
        "columnName": column,
        "rowNumber": row_num,
        "row": row,
        "message": _error_msg(rule, table, column, row_num),
    }
    error.update(extra)
    return error


def _gen_report_entry(e, row) -> str:
    rule_key = e.schema_path[-1]
    rule = _KEY_RULES.get(rule_key)
    assert rule, f"missing rule for constraint '{rule_key}'"
    (table, row_index, column) = e.document_path
    extra = {}
    if e.value:
        extra["invalidValue"] = e.value
    return _gen_rule_error(rule.id, table, column, row_index, row, extra)


def generate_cerberus_schema(parts) -> pt.Schema:
    schema = {}
    data = pt.gen_partdata(parts)
    for r in ruleset:
        s = r.gen_schema(data)
        assert s is not None
        utils.deep_update(s, schema)
    return schema


def validate_data(schema, data) -> Optional[ErrorList]:
    """
    Validates data with schema, using Cerberus.
    Returns list of errors or None on success.
    """
    # Unknown fields must be allowed because we're only generating a schema
    # for the requirements, not the optional data.
    v = Validator(schema)
    v.allow_unknown = True
    if v.validate(data):
        return

    report = []
    for table_error in v._errors:
        for row_errors in table_error.info:
            for e in row_errors:
                row = e.value
                for attr_errors in e.info:
                    for e in attr_errors:
                        report.append(_gen_report_entry(e, row))
    return report if len(report) > 0 else None
