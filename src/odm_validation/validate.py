import sys
from cerberus import Validator
from cerberus.errors import ValidationError, MAPPING_SCHEMA

__all__ = ["generate_cerberus_schema", "validate_data"]

# constants
ATTRIBUTE_KINDS = {"PK", "FK", "HEADER"}
NA = {"", "NA", "Not applicable"}


def stripRow(row: dict):
    return {k: v for k, v in row.items() if v not in NA}


def isTable(row):
    return row.get("partType") == "table"


def isAttribute(row):
    return row.get("partType") == "attribute"


def table_attr(attr_row, table_names) -> (str, str):
    """Returns list of (table_name, attr_kind)."""
    result = []
    for tname in table_names:
        val = attr_row.get(tname)
        if not val:
            continue
        ak = val.upper()
        if ak in ATTRIBUTE_KINDS:
            result.append((tname, ak))
    return result


def generate_cerberus_schema(sparseParts):
    parts = list(map(stripRow, sparseParts))
    tables = list(filter(isTable, parts))
    attributes = list(filter(isAttribute, parts))
    tableNames = [row["partID"] for row in tables]

    schema = {}
    for t in tableNames:
        schema[t] = {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {}
            },
            "meta": {
                "partID": t
            }
        }

    for row in attributes:
        id = row["partID"]
        for (table_name, attr_kind) in table_attr(row, tableNames):
            meta = {
                "partID": id,
                table_name: attr_kind,
            }
            t = {
                "meta": meta
            }
            reqKey = table_name + "Required"
            reqVal = row.get(reqKey)
            if reqVal == "Mandatory":
                t["required"] = True
                meta[reqKey] = reqVal
            schema[table_name]["schema"]["schema"][id] = t
    return schema


def missing_mandatory_column(e):
    assert type(e) is ValidationError
    if e.code != MAPPING_SCHEMA.code:
        return
    (table, row_index) = e.document_path
    column = e.info[0][0].schema_path[3]
    row_number = row_index + 1
    return {
        "errorType": sys._getframe().f_code.co_name,
        "tableName": table,
        "columnName": column,
        "rowNumber": row_number,
        "row": e.value,
        "validationRuleFields": e.constraint[column]["meta"],
        "message": f"Missing mandatory column {column} in table {table} " +
                   f"in row number {row_number}"
    }


def dummy_rule(e):
    return


def validate_data(schema, data) -> [dict]:
    """Returns list of errors or None on success"""
    v = Validator(schema)
    if v.validate(data):
        return
    rules = [
        dummy_rule,
        missing_mandatory_column
    ]
    report = []
    for table_error in v._errors:
        for row_errors in table_error.info:
            for e in row_errors:
                for rule in rules:
                    res = rule(e)
                    if res:
                        report.append(res)

    return report
