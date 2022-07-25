__all__ = ["generate_cerberus_schema"]

NA = {"", "NA", "Not applicable"}


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
            }
        }

    for row in attributes:
        id = row["partID"]
        tname = attrTable(row, tableNames)
        if tname is None:
            continue
        t = {}
        if row.get(tname + "Required") == "Mandatory":
            t["required"] = True
        schema[tname]["schema"]["schema"][id] = t
    return schema
