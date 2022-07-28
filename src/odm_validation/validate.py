import sys
from cerberus import Validator
from cerberus.errors import ValidationError, MAPPING_SCHEMA

# __all__ = ["generate_cerberus_schema", "validate_data"]

# constants
ATTRIBUTE_KINDS = {"PK", "FK", "HEADER"}
NA = {"", "NA", "Not applicable"}


def stripRow(row: dict):
    return {k: v for k, v in row.items() if v not in NA}


# def isTable(row):
#     return row.get("partType") == "table"


# def isAttribute(row):
#     return row.get("partType") == "attribute"


# def table_attr(attr_row, table_names) -> (str, str):
#     """Returns list of (table_name, attr_kind)."""
#     result = []
#     for tname in table_names:
#         val = attr_row.get(tname)
#         if not val:
#             continue
#         ak = val.upper()
#         if ak in ATTRIBUTE_KINDS:
#             result.append((tname, ak))
#     return result
#     rules = []
#     for t in table_names:
#         a = table_attr[t]
#         r = validation_rules.missing_mandatory_column(t, a)
#         rules.append(r)
#     return rules


def gen_rule_error(rules, cerberus_error):
    e = cerberus_error
    assert type(e) is ValidationError
    if e.code != MAPPING_SCHEMA.code:
        return
    (table, row_index) = e.document_path
    # column = e.info[0][0].schema_path[3]
    row_number = row_index + 1
    # meta = e.constraint[column]["meta"]
    # metaFields = meta.copy().delete("message")
    return {
        # "errorType": meta,
        "tableName": table,
        # "columnName": column,
        "rowNumber": row_number,
        "row": e.value,
        # "validationRuleFields": metaFields,
        # "message": f"Missing mandatory column {column} in table {table} " +
        #            f"in row number {row_number}"
    }


def validate_data(rules, schema, data) -> [dict]:
    """
    Validates data with schema, using Cerberus.
    Returns list of errors or None on success.
    """
    v = Validator(schema)
    if v.validate(data):
        return
    report = []
    for table_error in v._errors:
        for row_errors in table_error.info:
            for e in row_errors:
                res = gen_rule_error(e)
                if res:
                    report.append(res)
    for r in rules:
        if not r.validate:
            continue
        res = r.validate(data)
        if res:
            report.append(res)
    return report if report != [] else None
