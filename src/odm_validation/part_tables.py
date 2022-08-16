"""Part-table definitions."""

from dataclasses import dataclass
from typing import Dict, List


Row = dict
Dataset = List[Row]
Schema = dict  # A Cerberus validation schema


@dataclass(frozen=True)
class PartData:
    """
    An immutable cache of all datasets derived from the 'parts' dataset.
    The parts-list is stripped of empty values before generating this.
    """
    all_rows: Dataset  # all parts
    attr_rows: Dataset  # is_attr
    cat_rows: Dataset  # is_cat
    catset_values: Dict[str, List[str]]  # Ex: ["collection"] = ["flowPr", ...]
    catset_cat_rows: Dict[str, Dataset]  # is_cat, by catset name
    catset_attr_rows: Dataset  # is_catset_attr
    table_catset_attr_rows: Dict[str, Dataset]  # is_catset_attr, by table name
    table_attr_rows: Dict[str, Dataset]  # is_attr, by table name
    table_rows: Dataset  # is_table
    tables: List[str]  # table names


# constants
MANDATORY = "Mandatory"
NA = {"", "NA", "Not applicable"}


def is_table(p):
    return p.get("partType") == "table"


def is_attr(p):
    return p.get("partType") == "attribute"


def is_catset_attr(p):
    """
    A Category-set attribute contains a category from its category-set.
    This is analogous to a field with an 'enum' type.
    """
    return is_attr(p) and p.get("catSetID")


def is_cat(p):
    """
    Categories are the actual values of a category-set.
    This is analogous to the values of 'enum' types.

    Categories without a catSetID are ignored.
    """
    return p.get("partType") == "category" and p.get("catSetID")


def get_partID(p):
    return p["partID"]


def get_table_attr_rows(tables, attr_rows) -> dict:
    """Returns dict of table names and their attribute parts."""
    result = {}
    for t in tables:
        result[t] = []
    for attr_row in attr_rows:
        for t in tables:
            if attr_row.get(t):
                result[t].append(attr_row)
    return result


def strip(parts):
    result = []
    for row in parts:
        result.append({k: v for k, v in row.items() if v not in NA})
    return result


def gen_partdata(parts) -> PartData:
    # `parts` are stripped before processing. This is important for performance
    # and simplicity of implementation
    parts = strip(parts)

    table_rows = [x for x in parts if is_table(x)]
    tables = [row["partID"] for row in table_rows]
    attr_rows = [x for x in parts if is_attr(x)]
    table_attr_rows = get_table_attr_rows(tables, attr_rows)
    cat_rows = list(filter(is_cat, parts))

    catset_values = {}
    catset_attr_rows = list(filter(is_catset_attr, parts))
    for catset_row in catset_attr_rows:
        catset = catset_row["catSetID"]
        catset_cat_rows = [x for x in cat_rows if x["catSetID"] == catset]
        values = list(map(get_partID, catset_cat_rows))
        catset_values[catset] = values

    table_catset_attr_rows = {}
    for table in tables:
        table_catset_attr_rows[table] = [
            x for x in catset_attr_rows if x.get(table)]

    return PartData(
        all_rows=parts,
        attr_rows=attr_rows,
        cat_rows=cat_rows,
        catset_values=catset_values,
        catset_attr_rows=catset_attr_rows,
        catset_cat_rows=catset_cat_rows,
        table_attr_rows=table_attr_rows,
        table_catset_attr_rows=table_catset_attr_rows,
        table_rows=table_rows,
        tables=tables
    )


def init_table_schema(name, attr_schema):
    return {
        name: {
            "type": "list",  # each table has a list of rows
            "schema": {
                "type": "dict",  # each row is a dict
                "schema": attr_schema,
            },
        }
    }


def init_attr_schema(attr: str, cerb_rule: tuple):
    return {
        attr: {
            cerb_rule[0]: cerb_rule[1],
            # "meta": {
            #     "partID": attr,
            # }
        }
    }
