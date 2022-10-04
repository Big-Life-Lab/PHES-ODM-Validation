"""Part-table definitions."""

from pprint import pprint

from dataclasses import dataclass
from logging import debug, error
from semver import Version
from typing import Dict, List, Set

import utils
from utils import meta_get, meta_mark, meta_pop
from versions import MapKind, get_mapping, is_compatible, parse_version


# type aliases
Row = dict
Dataset = List[Row]
Schema = dict  # A Cerberus validation schema


@dataclass(frozen=True)
class CatsetData:
    """Data for each category set."""
    meta: list
    tables: Set[str]  # tables in which this catset is used
    values: List[str]  # Ex: ['collection'] = ['flowPr', ...]


@dataclass(frozen=True)
class TableData:
    """Data for each table."""
    attributes: Dict[str, Dataset]


@dataclass(frozen=True)
class PartData:
    """
    An immutable cache of all datasets derived from the 'parts' dataset.
    The parts-list is stripped of empty values before generating this.
    """
    all_parts: Dataset
    attributes: Dataset
    catset_data: Dict[str, CatsetData]  # category-set data, by attr name
    table_data: Dict[str, TableData]  # table data, by table name
    # meta: Dict[str, dict]  # meta data, by part id


# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

# field constants
CATSET_ID = 'catSetID'
PART_ID = 'partID'
PART_TYPE = 'partType'

PART_ID_ORIGINAL = 'partID_original'
TABLE_ID_ORIGINAL = 'tableID_original'
TABLE_REQUIRED_ORIGINAL = 'tableRequired_original'

_ORIGINAL_KEY = '_original_key'
_ORIGINAL_VAL = '_original_val'

# partType constants
ATTRIBUTE = 'attribute'
CATEGORY = 'category'
TABLE = 'table'

# other value constants
MANDATORY = 'mandatory'
NA = {'', 'NA', 'Not applicable'}


def table_required_field(table_name):
    return table_name + 'Required'


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


V1_FIELD_PREFIX = 'version1'


def get_catset_meta(row):
    """Returns metadata for category-sets and its categories/values."""
    fields = [PART_ID, PART_TYPE, CATSET_ID]
    return {key: row[key] for key in fields}


def get_catset_tables(row: Row, table_names: List[str]) -> List[str]:
    result = []
    for table in table_names:
        if row.get(table):
            result.append(table)
    return result


def get_table_id(part: dict, meta) -> str:
    if is_table(part):
        return meta_get(part, PART_ID)
    else:
        req = list(filter(lambda k: k.endswith('Required'), part.keys()))[0]
        meta_mark(meta, part, req)
        return req[:req.find('Required')]


def strip(parts: Dataset):
    """Removes NA fields."""
    result = []
    for sparse_row in parts:
        row = {k: v for k, v in sparse_row.items() if v not in NA}
        result.append(row)
    return result


def filter_compatible(parts: Dataset, version: Version) -> Dataset:
    """Filters `parts` by `version`."""
    result = []
    for row in parts:
        if not (get_mapping(row, version) or is_compatible(row, version)):
            print(f'skipping incompatible part: {get_partID(row)}')
            continue
        result.append(row)
    return result


def replace_id(part: dict, part_id0: str, part_id1: str) -> dict:
    part[PART_ID + _ORIGINAL_VAL] = part_id0
    part[PART_ID] = part_id1
    # inv[part_id1] = part_id0


def replace_table_id(part: dict, table_id0: str, table_id1: str, meta
                     ) -> dict:
    assert not is_table(part), 'use `replace_table_id` instead'

    # replace <table> field
    column_kind = meta_pop(meta, part, table_id0)
    part[table_id1] = column_kind
    part[table_id1 + _ORIGINAL_KEY] = table_id0
    # inv[table_id1] = {table_id0: column_kind}

    # replace <table>Required field
    req_key0 = table_required_field(table_id0)
    req_val0 = meta_pop(meta, part, req_key0)
    req_key1 = table_required_field(table_id1)
    part[req_key1] = req_val0
    part[req_key1 + _ORIGINAL_KEY] = req_key0
    part[req_key1 + _ORIGINAL_VAL] = req_val0
    # inv[req_key1] = {req_key0: req_val0}


def transform_v2_to_v1(parts0: Dataset) -> (Dataset, dict):
    """Transforms v2 parts to v1, based on `version1*` fields.

    :parts0: stripped parts

    Returns (new_parts, parts_meta).
    """
    parts1 = []
    # inverse = {}
    meta = {}
    version = Version(major=1)
    for p0 in parts0:
        mapping = get_mapping(p0, version)

        # TODO
        if mapping.kind == MapKind.CATEGORY:
            error(f'{mapping.kind} is not yet implemented')
            p1 = p0
            continue

        p1 = p0.copy()
        pid0 = p0[PART_ID]
        pid1 = mapping.id
        replace_id(p1, pid0, pid1)
        if not is_table(p1):
            table0 = get_table_id(p0, meta)
            table1 = mapping.table
            replace_table_id(p1, table0, table1, meta)

        parts1.append(p1)
    return (parts1, meta)


def gen_partdata(parts: Dataset) -> PartData:
    """
    :parts: From v2. Must be stripped.
    """

    # `parts` are assumed to be from ODM v2.
    # `parts` must be stripped.

    tables = list(filter(is_table, parts))
    table_names = list(map(get_partID, tables))
    attributes = list(filter(is_attr, parts))
    table_attr = get_table_attr(table_names, attributes)
    categories = list(filter(is_cat, parts))
    catsets = list(filter(is_catset_attr, parts))

    catset_data = {}
    for cs in catsets:
        attr_id = cs[PART_ID]
        cs_id = cs[CATSET_ID]
        cats = [c for c in categories if c[CATSET_ID] == cs_id]
        used_rows = [cs] + cats
        meta = list(map(get_catset_meta, used_rows))
        tables = set(get_catset_tables(cs, table_names))
        values = list(map(get_partID, cats))
        catset_data[attr_id] = CatsetData(
            meta=meta,
            tables=tables,
            values=values,
        )

    table_data = {}
    for id in table_names:
        table_data[id] = TableData(
            attributes=table_attr[id],
        )

    # meta = {p[PART_ID]: p['meta'] for p in parts}

    return PartData(
        all_parts=parts,
        attributes=attributes,
        catset_data=catset_data,
        table_data=table_data,
        # meta=meta,
    )


def init_table_schema(name, attr_schema):
    return {
        name: {
            'type': 'list',  # each table has a list of rows
            'schema': {
                'type': 'dict',  # each row is a dict
                'schema': attr_schema,
            },
        }
    }


def init_attr_schema(attr_id: str, rule_id: str, cerb_rule: tuple,
                     meta: List[dict] = []):
    return {
        attr_id: {
            cerb_rule[0]: cerb_rule[1],
            'meta': [
                {
                    'ruleID': rule_id,
                    'meta': meta,
                }
            ]
        }
    }


def update_schema(schema, table_id, attr_id, rule_id, cerb_rule, meta):
    attr_schema = init_attr_schema(attr_id, rule_id, cerb_rule, meta)
    table_schema = init_table_schema(table_id, attr_schema)
    utils.deep_update(table_schema, schema)
