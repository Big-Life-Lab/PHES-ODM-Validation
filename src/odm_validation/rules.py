# rules
# - must have access to the whole input doc
# - the rule is not actually checking the data, it's only setting cerberus schema attributes.
# - if cerberus is unable to do the checks then the rule has to do that too.

# - rule must

from dataclasses import dataclass
from typing import Callable

# {{{1 Types

Document = [dict]  # The input data
Schema = dict  # A Cerberus validation schema
RowSet = dict
ValidateFunc = Callable[Document, str]


@dataclass
class Rule:
    """
    A rule needs to be able to do the following:
    - generate a Cerberus validation schema for table fields (with msg)
    - validate a document (with msg)
    - a way to find the rule from cerberus error (if not using custom validation)
        - rule.schema can be filter
    """
    schema: Schema = None  # cerberus schema for all the tables
    message: str = ""   # cerberus error message
    validate: ValidateFunc = None  # for custom validation


def init_table_schema(name, row_schema):
    return {
        name: {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": row_schema,
            }
        }
    }


def missing_mandatory_column(table, table_attr) -> Rule:
    """checks that a table has all its mandatory fields"""
    assert type(table_attr) is list
    tableSchema = {}
    required = table + "Required"
    for part in table_attr:
        id = part.get("partID")
        if part.get(required) == "Mandatory":
            fieldSchema = {id: {"required": True}}
            tableSchema.update(fieldSchema)
    schema = {table: tableSchema} if tableSchema != {} else None
    msg = f"Missing mandatory column in table {table}."
    return Rule(schema=schema, message=msg)


def invalid_address_country():
    schema = init_table_schema("addresses", {
        "country": {
            "type": "list",
            "allowed": ["Canada"]
        }
    })
    msg = "Invalid country in address."
    return Rule(schema=schema, message=msg)


def duplicate_primary_key(tablePks) -> Rule:
    def validate(doc) -> [str]:
        assert type(doc) is dict
        errors = []
        for table, rows in doc.items():
            pk = tablePks[table]
            ids = set()
            for row in rows:
                id = row.get(pk)
                if id in ids:
                    msg = f"duplicate id {id} in row x"
                    errors.append(msg)
                ids.add(id)
        return errors if len(errors) else None

    return Rule(validate=validate)

# data = {
#     "addresses": [
#         {
#             "addressID": "1",
#             # "datasetID": "2",
#             "city": "Ottawa",
#             "country": "Canada",
#         },
#         {
#             "addressID": "1",
#             "datasetID": "2",
#             "city": "Ottawa",
#             "country": "Canada",
#             "addL2": "12345 Lane Avenue",
#         }
#     ],
#     "contacts": [
#         {
#             # "contactID": "1",
#             "organizationID": "1",
#         }
#     ]
# }


# tables = ["addresses", "contacts"]
# parts = [
#     {"partID": "addressID", "addressesRequired": "Mandatory"},
#     {"partID": "contactID", "contactsRequired": "Mandatory"},
# ]
# i = 0
# for table in tables:
#     tableParts = [parts[i]]
#     r = missing_mandatory_column(table, tableParts)
#     print(r.schema)
#     i += 1

# tablePks = {"addresses": "addressID", "contacts": "contactID"}
# r = duplicate_primary_key(tablePks)
# print(r.validate(data))


# # def add_rule(rule):



# # def rule_MissingMandatoryColumn(ctx):
# #     key = ctx.table + "Required"
# #     val = ctx.row.get(key)
# #     if not val or val != "Mandatory":
# #         return
# #     id = ctx.row["partID"]
# #     ctx.schema["required"] = True
# #     ctx.schema["meta"][key] = val
# #     ctx.schema["meta"]["message"] = \
# #         f"Missing mandatory column {id} in table {ctx.table} " +\
# #         "in row number {row_number}"


# # schema = {"meta": {"partID": "addressID", "addresses": "PK"}}
# # ctx = Context("addresses", {"addressesRequired": "Mandatory"}, schema)
# # rule_MissingMandatoryColumn(ctx)
# # print(schema)
