"""Part-table definitions."""

import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import partial
from logging import warning
from operator import is_not
from pprint import pprint
from semver import Version
from typing import DefaultDict, Dict, List, Set

import utils
from versions import parse_version


# type aliases
PartId = str
Row = dict
Dataset = List[Row]
MetaEntry = Dict[str, str]
Meta = List[MetaEntry]
MetaMap = DefaultDict[PartId, Meta]
Schema = dict  # A Cerberus validation schema


class MapKind(Enum):
    TABLE = 0
    ATTRIBUTE = 1
    CATEGORY = 2


class ColumnKind(Enum):
    PK = "pK"
    FK = "fK"
    HEADER = "header"
    INPUT = "input"


# TODO: rename id to part_id?
@dataclass(frozen=True)
class Mapping:
    kind: MapKind
    id: str
    table: str
    meta_entry: MetaEntry


@dataclass(frozen=True)
class CatsetData:
    """Data for each category set."""
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
    meta: MetaMap


# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

COLUMN_KINDS = set(list(map(lambda e: e.value, ColumnKind)))

# field constants
CATSET_ID = 'catSetID'
PART_ID = 'partID'
PART_TYPE = 'partType'

PART_ID_ORIGINAL = 'partID_original'
TABLE_ID_ORIGINAL = 'tableID_original'
TABLE_REQUIRED_ORIGINAL = 'tableRequired_original'

# suffixes
_ORIGINAL_KEY = '_original_key'
_ORIGINAL_VAL = '_original_val'
_REQUIRED = 'Required'

# partType constants
ATTRIBUTE = 'attribute'
CATEGORY = 'category'
TABLE = 'table'

# other value constants
MANDATORY = 'mandatory'
NA = {'', 'NA', 'Not applicable'}

# mapping
V1_KIND_MAP = {
    'tables': MapKind.TABLE,
    'variables': MapKind.ATTRIBUTE,
    'variableCategories': MapKind.CATEGORY,
}


def parse_row_version(row, field, default=None):
    return parse_version(row.get(field), row.get('partID'), field, default)


def is_compatible(part: dict, version: Version) -> bool:
    # TODO: remove default for `firstReleased` when parts-v2 is complete
    row = part
    v1 = Version(major=1)
    first = parse_row_version(row, 'firstReleased', default=v1)
    last = parse_row_version(row, 'lastUpdated', default=first)
    active: bool = row.get('status') == 'active'

    # not (v < first) and ((v < last) or active)
    v = version
    if v.compare(first) < 0:
        return False
    if v.compare(last) < 0:
        return True
    return active


def _get_original_key_val(part, key, val=None):
    key_orig = part.get(key + _ORIGINAL_KEY)
    val_orig = part.get(key + _ORIGINAL_VAL)
    if key_orig:
        key = key_orig
    if val_orig:
        val = val_orig
    elif not val:
        val = part.get(key)
    return (key, val)


def meta_mark(meta: MetaEntry, part, key, val=None):
    (key, val) = _get_original_key_val(part, key, val)
    meta[key] = val


def meta_get(meta: MetaEntry, part, key):
    """returns `part[key]` and records the retrival in `meta`"""
    val = part.get(key)
    if val is not None:
        assert val is not None
        meta_mark(meta, part, key, val)
        return val


def meta_pop(meta: MetaEntry, part, key):
    """same as `meta_get` but also removes `key` from `part`."""
    result = meta_get(meta, part, key)
    del part[key]
    return result


def parse_version1Category(s: str) -> List[str]:
    cats = s.split(';')
    return list(map(str.strip, cats))


def get_mappings(part: dict, version: Version) -> List[Mapping]:
    """Returns `None` when no mapping exists."""
    result = []
    if version.major != 1:
        return
    m: MetaEntry = {}
    table = meta_get(m, part, 'version1Table')
    loc = meta_get(m, part, 'version1Location')
    kind = V1_KIND_MAP.get(loc)
    if kind == MapKind.TABLE:
        ids = [table]
    elif kind == MapKind.ATTRIBUTE:
        ids = [meta_get(m, part, 'version1Variable')]
    elif kind == MapKind.CATEGORY:
        ids = parse_version1Category(meta_get(m, part, 'version1Category'))
    for id in filter(partial(is_not, None), ids):
        result.append(Mapping(kind=kind, id=id, table=table, meta_entry=m))
    return result


def has_mapping(part: dict, version: Version) -> bool:
    ms = get_mappings(part, version)
    return ms and len(ms) > 0


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


def get_catset_tables(row: Row, table_names: List[str], meta: MetaEntry
                      ) -> List[str]:
    result = []
    for table in table_names:
        if meta_get(meta, row, table):
            result.append(table)
    return result


def get_key(pair):
    return pair[0]


def get_val(pair):
    return pair[1]


def get_table_id(part: dict, meta) -> str:
    """ Retrieves the table id of `part`.

    The value is looked up in the following order:

    1. partID & partType
    2. <table>Required
    3. <table>:<column_kind>

    :raises Exception: when table info is missing.
    """
    if is_table(part):
        return meta_get(meta, part, PART_ID)
    req_keys = list(filter(lambda k: k.endswith(_REQUIRED), part.keys()))
    if len(req_keys) > 0:
        req = req_keys[0]
        meta_mark(meta, part, req)
        return req[:req.find(_REQUIRED)]
    column_keys = list(
        map(get_key,
            filter(lambda pair: get_val(pair) in COLUMN_KINDS, part.items())))
    if len(column_keys) > 0:
        return column_keys[0]
    raise Exception(f'part {get_partID(part)} is missing table info')


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
        if not (is_compatible(row, version) or has_mapping(row, version)):
            warning(f'skipping incompatible part: {get_partID(row)}')
            continue
        result.append(row)
    return result


def replace_id(part: dict, part_id0: str, part_id1: str) -> dict:
    part[PART_ID + _ORIGINAL_VAL] = part_id0
    part[PART_ID] = part_id1


def replace_table_id(part: dict, table_id0: str, table_id1: str, meta
                     ) -> dict:
    assert not is_table(part), 'use `replace_table_id` instead'

    # replace <table> field
    column_kind = meta_pop(meta, part, table_id0)
    part[table_id1] = column_kind
    part[table_id1 + _ORIGINAL_KEY] = table_id0

    # replace <table>Required field (optional)
    req_key0 = table_required_field(table_id0)
    if part.get(req_key0):
        req_val0 = meta_pop(meta, part, req_key0)
        req_key1 = table_required_field(table_id1)
        part[req_key1] = req_val0
        part[req_key1 + _ORIGINAL_KEY] = req_key0
        part[req_key1 + _ORIGINAL_VAL] = req_val0


def transform_v2_to_v1(parts0: Dataset, meta: MetaMap) -> (Dataset, MetaMap):
    """Transforms v2 parts to v1, based on `version1*` fields.

    :parts0: stripped parts

    Returns (new_parts, parts_meta).
    """
    parts1 = []
    version = Version(major=1)
    for p0 in parts0:
        for mapping in get_mappings(p0, version):
            p1 = p0.copy()
            m: MetaEntry = mapping.meta_entry.copy()
            pid0 = meta_get(m, p0, PART_ID)
            pid1 = mapping.id
            replace_id(p1, pid0, pid1)
            if is_attr(p1):
                table0 = get_table_id(p0, m)
                table1 = mapping.table
                replace_table_id(p1, table0, table1, m)
            parts1.append(p1)
            meta[pid1].append(m)
    return (parts1, meta)


# def get_or_put(d: dict, key, default_val):
#     val = d.get(key)
#     if val is None:
#         val = default_val
#         d[key] = val
#     return val


def gen_partdata(parts: Dataset, meta: MetaMap):
    """
    :parts: From v2. Must be stripped.
    :meta: meta, by attr id
    """
    tables = list(filter(is_table, parts))
    table_names = list(map(get_partID, tables))
    attributes = list(filter(is_attr, parts))
    table_attr = get_table_attr(table_names, attributes)
    categories = list(filter(is_cat, parts))
    catsets = list(filter(is_catset_attr, parts))

    catset_data = {}
    for cs in catsets:
        m: MetaEntry = {}
        attr_id = meta_get(m, cs, PART_ID)
        cs_id = meta_get(m, cs, CATSET_ID)
        cats = [c for c in categories if meta_get(m, c, CATSET_ID) == cs_id]
        tables = set(get_catset_tables(cs, table_names, m))
        values = list(map(get_partID, cats))
        catset_data[attr_id] = CatsetData(
            tables=tables,
            values=values,
        )
        meta[attr_id].append(m)

    table_data = {}
    for id in table_names:
        table_data[id] = TableData(
            attributes=table_attr[id]
        )

    return PartData(
        all_parts=parts,
        attributes=attributes,
        catset_data=catset_data,
        table_data=table_data,
        meta=meta,
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


def init_table_schema_meta(name, meta: Meta):
    return {
        name: {
            'schema': {
                'meta': meta
            },
        }
    }


def init_attr_schema(attr_id: str, rule_id: str, cerb_rule: tuple, meta: Meta):
    return {
        attr_id: {
            cerb_rule[0]: cerb_rule[1],
            'meta': [
                {
                    'ruleID': rule_id,
                    'meta': meta,
                },
                # {
                #     'ruleID': another_rule_using_this_attr,
                #     'meta': [
                #         meta_for_attr_used_with_this_rule,
                #         meta_for_another_attr_used_with_this_rule,
                #     ]
                # }
            ]
        }
    }


def deduplicate_meta(meta: Meta) -> Meta:
    """merges meta entries with the same part id"""
    id_entry: Dict[str, MetaEntry] = {}
    for entry in meta:
        id = entry[PART_ID]
        if id in id_entry:
            id_entry[id] |= entry
        else:
            id_entry[id] = entry
    return [val for key, val in id_entry.items()]


def update_schema(schema, table_id, attr_id, rule_id, cerb_rule, meta: Meta):
    assert isinstance(meta, list)
    assert len(meta[0]) > 0
    assert isinstance(meta[0], dict), type(meta[0])
    meta = deduplicate_meta(meta)
    attr_schema = init_attr_schema(attr_id, rule_id, cerb_rule, meta)
    table_schema = init_table_schema(table_id, attr_schema)
    utils.deep_update(table_schema, schema)
