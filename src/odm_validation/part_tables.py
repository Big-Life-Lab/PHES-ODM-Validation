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
    cat_values: Dict[str, List[str]]  # Ex: ["collection"] = ["flowPr", ...]
    table_attr_rows: Dict[str, Dataset]  # is_attr, by table name
    table_cat_attr_rows: Dict[str, Dataset]  # is_attr && catSetID, by tbl name
    table_rows: Dataset  # is_table
    tables: List[str]  # table names


# constants
MANDATORY = "Mandatory"
NA = {"", "NA", "Not applicable"}


def is_table(p):
    return p.get("partType") == "table"


def is_attr(p):
    return p.get("partType") == "attribute"


def is_cat_val(p):
    return p.get("partType") == "category"


def is_catset_attr(p):
    return is_attr(p) and p.get("catSetID")


def get_partID(p):
    return p.get("partID")


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


def get_category_values(parts, cat):
    return list(
        map(get_partID,
            filter(lambda x: is_cat_val(x) and x.get("catSetID") == cat,
                   parts)))


def get_catset_attributes(parts: list, table: str):
    return [x for x in parts if x.get(table) and is_catset_attr(x)]


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

    cat_values = {}
    table_cat_attr_rows = {}
    for table in tables:
        catset_attr_rows = get_catset_attributes(parts, table)
        for attr_row in catset_attr_rows:
            cat = attr_row.get("catSetID")
            cat_values[cat] = get_category_values(parts, cat)
        table_cat_attr_rows[table] = catset_attr_rows

    return PartData(
        all_rows=parts,
        attr_rows=attr_rows,
        cat_values=cat_values,
        table_attr_rows=table_attr_rows,
        table_cat_attr_rows=table_cat_attr_rows,
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
