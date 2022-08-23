"""Part-table definitions."""

from dataclasses import dataclass
from typing import Dict, List


# type aliases
Row = dict
Dataset = List[Row]
Schema = dict  # A Cerberus validation schema


@dataclass(frozen=True)
class PartData:
    """
    An immutable cache of all datasets derived from the 'parts' dataset.
    The parts-list is stripped of empty values before generating this.
    """
    all_parts: Dataset
    attributes: Dataset
    catset_values: Dict[str, List[str]]  # Ex: ["collection"] = ["flowPr", ...]
    catset_meta: Dict[str, list]  # meta, by catset name
    table_catset_attr: Dict[str, Dataset]  # is_catset_attr, by tbl name
    table_attr: Dict[str, Dataset]  # is_attr, by table name
    table_names: List[str]


# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

# field constants
CATSET_ID = "catSetID"
PART_ID = "partID"
PART_TYPE = "partType"

# partType constants
ATTRIBUTE = "attribute"
CATEGORY = "category"
TABLE = "table"

# other value constants
MANDATORY = "Mandatory"
NA = {"", "NA", "Not applicable"}


def table_required_field(table_name):
    return table_name + "Required"


def has_catset(p):
    return p.get(CATSET_ID) is not None


def is_table(p):
    return p.get(PART_TYPE) == TABLE


def is_attr(p):
    return p.get(PART_TYPE) == ATTRIBUTE


def is_catset_attr(p):
    """
    A Category-set attribute is the name of a collection of values.
    This is analogous to an 'enum' type.
    """
    return is_attr(p) and has_catset(p)


def is_cat(p):
    """
    Categories are the actual values of a category-set.
    This is analogous to the values of 'enum' types.

    Categories without a catSetID are invalid and ignored.
    """
    return p.get(PART_TYPE) == CATEGORY and has_catset(p)


def get_partID(p):
    return p[PART_ID]


def get_table_attr(table_names, attributes) -> dict:
    """Returns dict of table names and their attribute parts."""
    result = {}
    for t in table_names:
        result[t] = []
    for attr in attributes:
        for t in table_names:
            if attr.get(t):
                result[t].append(attr)
    return result


def strip(parts):
    result = []
    for row in parts:
        result.append({k: v for k, v in row.items() if v not in NA})
    return result


def get_catset_meta(row):
    """Returns metadata for category-sets and its categories/values."""
    fields = [PART_ID, PART_TYPE, CATSET_ID]
    return {key: row[key] for key in fields}


def gen_partdata(parts) -> PartData:
    # `parts` are stripped before processing. This is important for performance
    # and simplicity of implementation
    parts = strip(parts)

    tables = list(filter(is_table, parts))
    table_names = list(map(get_partID, tables))
    attributes = list(filter(is_attr, parts))
    table_attr = get_table_attr(table_names, attributes)
    categories = list(filter(is_cat, parts))
    catsets = list(filter(is_catset_attr, parts))

    catset_values = {}
    catset_meta = {}
    for cs in catsets:
        id = cs[CATSET_ID]
        cats = [c for c in categories if c[CATSET_ID] == id]
        values = list(map(get_partID, cats))
        catset_values[id] = values
        used_rows = [cs] + cats
        catset_meta[id] = list(map(get_catset_meta, used_rows))

    table_catset_attr = {}
    for t in table_names:
        table_catset_attr[t] = [cs for cs in catsets if cs.get(t)]

    return PartData(
        all_parts=parts,
        attributes=attributes,
        catset_values=catset_values,
        catset_meta=catset_meta,
        table_attr=table_attr,
        table_catset_attr=table_catset_attr,
        table_names=table_names
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


def init_attr_schema(rule_id: str, cerb_rule: tuple, attr: Row,
                     meta: List[dict] = []):
    attr_id = get_partID(attr)
    return {
        attr_id: {
            cerb_rule[0]: cerb_rule[1],
            "meta": [
                {
                    "ruleID": rule_id,
                    "meta": [{PART_ID: attr_id}] + meta,
                }
            ]
        }
    }
