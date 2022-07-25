# TODO:
# - document inflect package requirement

import sys
import inflect
from cerberus import Validator
from cerberus.errors import ValidationError, SEQUENCE_SCHEMA

__all__ = ["generate_cerberus_schema", "validate_data"]

NA = {"", "NA", "Not applicable"}

grammar = inflect.engine()

def stripRow(row: dict):
    return {k: v for k, v in row.items() if v not in NA}


def isTable(row):
    return row.get("partType") == "table"


def isAttribute(row):
    return row.get("partType") == "attribute"


def attrTable(attr, tableNames):
    for name in tableNames:
        t = attr.get(name)
        if t and t.upper() == "PK":
            return name


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
        tname = attrTable(row, tableNames)
        if tname is None:
            continue
        meta = {
            "partID": id,
            tname: "PK",
        }
        t = {
            "meta": meta
        }
        reqKey = tname + "Required"
        reqVal = row.get(reqKey)
        if reqVal == "Mandatory":
            t["required"] = True
            meta[reqKey] = reqVal
        schema[tname]["schema"]["schema"][id] = t
    return schema


def missing_mandatory_column(e):
    assert type(e) is ValidationError
    if e.code != SEQUENCE_SCHEMA.code:
        return
    (table, row_index) = e.info[0][0].document_path
    column = grammar.singular_noun(table) + "ID"
    row_number = row_index + 1
    return {
        "errorType": sys._getframe().f_code.co_name,
        "tableName": table,
        "columnName": column,
        "rowNumber": row_number,
        "row": dict(e.value[row_index]),
        "validationRuleFields": e.constraint["schema"][column]["meta"],
        "message": f"Missing mandatory column {column} in table {table} " +
                   f"in row number {row_number}"
    }


def dummy_rule(e):
    return


def validate_data(schema, data):
    v = Validator(schema)
    if v.validate(data):
        return
    rules = [
        dummy_rule,
        missing_mandatory_column
    ]
    report = []
    for e in v._errors:
        for rule in rules:
            res = rule(e)
            if res:
                report.append(res)
    return report
