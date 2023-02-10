"""Part-table definitions."""

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import islice
from logging import error, warning
from os.path import join, normpath
from pathlib import Path
from semver import Version
from typing import DefaultDict, Dict, List, Optional, Set
# from pprint import pprint

from stdext import flatten
from versions import parse_version


# type aliases (primitive)
BoolSet = Set[str]  # a set of boolean values
Part = dict
PartId = str
Row = dict

# type aliases (meta)
MetaEntry = Dict[str, str]
Meta = List[MetaEntry]
MetaMap = DefaultDict[PartId, Meta]

# type aliases (other)
Dataset = List[Row]
PartMap = Dict[PartId, Part]
TableId = PartId


class MapKind(Enum):
    TABLE = 0
    ATTRIBUTE = 1
    CATEGORY = 2


class ColumnKind(Enum):
    PK = "pK"
    FK = "fK"
    HEADER = "header"
    INPUT = "input"


@dataclass(frozen=True)
class CatsetData:
    """Data for each category set."""
    part: Part
    table_ids: Set[str]  # tables in which this catset is used
    cat_parts: List[Part]  # the parts belonging to this catset
    cat_values: List[str]  # Ex: category set `coll` has ['flowPr', ...]


@dataclass(frozen=True)
class TableData:
    """Data for each table."""
    part: Part
    attributes: PartMap


@dataclass(frozen=True)
class PartData:
    """
    An immutable cache of all datasets derived from the 'parts' dataset.
    The parts-list is stripped of empty values before generating this.
    """
    bool_set: BoolSet
    null_set: Set[str]
    catset_data: Dict[PartId, CatsetData]  # category-set data, by catset id
    table_data: Dict[PartId, TableData]  # table data, by table id
    mappings: Dict[PartId, List[PartId]]  # v1 mapping, by part id


def _get_latest_odm_version_str() -> str:
    file_path = normpath(os.path.realpath(__file__))
    root_dir = join(os.path.dirname(file_path), '../..')
    dict_dir = join(root_dir, 'assets/dictionary')
    versions = []
    for dir_path in Path(dict_dir).glob('v*'):
        dir_name = os.path.basename(dir_path)
        if not (match := re.search('v(.+)', dir_name)):
            continue
        v = parse_version(match.group(1), verbose=False)
        versions.append(str(v))
    if len(versions) == 0:
        sys.exit("failed to get latest ODM version")
    versions.sort()
    return versions[-1]


# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

COLUMN_KINDS = set(list(map(lambda e: e.value, ColumnKind)))
ODM_VERSION_STR = _get_latest_odm_version_str()
ODM_VERSION = parse_version(ODM_VERSION_STR)

# field constants
CATSET_ID = 'catSetID'
DATA_TYPE = 'dataType'
PART_ID = 'partID'
PART_TYPE = 'partType'
STATUS = 'status'

PART_ID_ORIGINAL = 'partID_original'
TABLE_ID_ORIGINAL = 'tableID_original'
TABLE_REQUIRED_ORIGINAL = 'tableRequired_original'

# suffixes
_REQUIRED = 'Required'

# partType constants
ATTRIBUTE = 'attribute'
CATEGORY = 'category'
TABLE = 'table'

# other value constants
ACTIVE = 'active'
BOOLEAN = 'boolean'
BOOLEAN_SET = 'booleanSet'
DATETIME = 'datetime'
MANDATORY = 'mandatory'
MISSINGNESS = 'missingness'
PART_NULL_SET = {'', 'NA', 'Not applicable', 'null'}

V1_VARIABLE = 'version1Variable'
V1_LOCATION = 'version1Location'
V1_TABLE = 'version1Table'
V1_CATEGORY = 'version1Category'


# mapping
V1_KIND_MAP = {
    'tables': MapKind.TABLE,
    'variables': MapKind.ATTRIBUTE,
    'variableCategories': MapKind.CATEGORY,
}


def get_validation_rule_fields(column_meta, rule_ids: List[str]):
    if not column_meta:
        return []
    assert isinstance(column_meta, list)
    assert isinstance(column_meta[0], dict)
    assert isinstance(column_meta[0]['meta'], list)
    return flatten(list(
        map(lambda x: x['meta'],
            filter(lambda x: x['ruleID'] in rule_ids,
                   column_meta))))


def parse_row_version(row, field, default=None):
    return parse_version(row.get(field), row.get('partID'), field, default)


def get_version_range(part: dict) -> (Version, Version):
    # TODO: remove default for `firstReleased` when parts-v2 is complete
    row = part
    v1 = Version(major=1)
    first = parse_row_version(row, 'firstReleased', default=v1)
    last = parse_row_version(row, 'lastUpdated', default=first)
    return (first, last)


def is_compatible(part, version: Version) -> bool:
    """Returns True if part is compatible with `version`."""
    # XXX: prerelease (like rc.3, etc.) must be stripped from `version`
    # before compare, because `v2.0.0-rc.3` < `v.2.0.0`.
    # logic: not (v < first) and ((v < last) or active)
    v = version
    v._prerelease = None
    first, last = get_version_range(part)
    active = (part.get(STATUS) == ACTIVE)
    if v.compare(first) < 0:
        return False
    if v.compare(last) < 0:
        return True
    return active


def _parse_version1Field(part, key) -> List[str]:
    val = part.get(key)
    if not val:
        return []
    raw_ids = val.split(';')
    return list(map(str.strip, raw_ids))


def get_mappings(part: dict, version: Version) -> Optional[List[PartId]]:
    """Returns a list of part ids from `version` corresponding to `part`,
    or None if there is no mapping."""
    # XXX: Parts may be missing version1 fields.
    # XXX: The 'booleanSet' is not required to have a version1Location.
    if version.major != 1:
        return
    ids = []
    loc = part.get(V1_LOCATION)
    kind = V1_KIND_MAP.get(loc)
    try:
        if kind == MapKind.TABLE:
            ids = _parse_version1Field(part, V1_TABLE)
        elif kind == MapKind.ATTRIBUTE:
            ids = _parse_version1Field(part, V1_VARIABLE)
        elif kind == MapKind.CATEGORY or is_bool_set(part):
            ids = _parse_version1Field(part, V1_CATEGORY)
    except KeyError:
        return
    if len(list(filter(lambda id: id and id != '', ids))) == 0:
        return
    return ids


def has_mapping(part: dict, version: Version) -> bool:
    ms = get_mappings(part, version)
    return ms and len(ms) > 0


def table_required_field(table_name):
    return table_name + 'Required'


def has_catset(p):
    return p.get(CATSET_ID) is not None


def is_bool_set(part):
    return part.get(CATSET_ID) == BOOLEAN_SET


def is_null_set(part):
    # the ODM doesn't have these values as a catset, but it's a set
    return part.get(PART_TYPE) == MISSINGNESS


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
    # TODO: rename to get_partid or get_id?
    assert PART_ID in p, str(p)
    return p[PART_ID]


def get_catset_table_ids(row: Row, table_ids: List[str]) -> List[str]:
    result = []
    for table in table_ids:
        if row.get(table):
            result.append(table)
    return result


def get_key(pair):
    return pair[0]


def get_val(pair):
    return pair[1]


def _get_table_id(part: dict) -> Optional[str]:
    """Retrieves the table id of `part`.

    It is looked up in the following order:

    1. partID & partType
    2. <table>Required
    3. <table>:<column_kind>
    """
    # The returned id must match a corresponding part with
    # partId=id and partType=table.
    if is_table(part):
        return part[PART_ID]
    req_keys = list(filter(lambda k: k.endswith(_REQUIRED), part.keys()))
    if len(req_keys) > 0:
        req = req_keys[0]
        return req[:req.find(_REQUIRED)]
    column_keys = list(
        map(get_key,
            filter(lambda pair: get_val(pair) in COLUMN_KINDS, part.items())))
    if len(column_keys) > 0:
        return column_keys[0]
    warning(f'part {get_partID(part)} does not belong to any table')


def _not_empty(field):
    _, val = field
    return val not in PART_NULL_SET


def strip(parts: Dataset):
    """Removes null fields, except from partID."""
    # 'partID' may be defining null fields for data, so we can't strip those.
    # TODO: Strip version1* fields when not version 1.
    result = []
    for sparse_row in parts:
        fields = iter(sparse_row.items())
        part_id_pair = next(fields)
        assert part_id_pair[0] == PART_ID, 'partID must be the first column'
        row = {k: v for k, v in filter(_not_empty, fields)}
        row[PART_ID] = part_id_pair[1]
        result.append(row)
    return result


def filter_compatible(parts: Dataset, schema_version: Version) -> Dataset:
    """Filters `parts` by `version`."""
    result = []
    for row in parts:
        part_id = get_partID(row)
        if not (is_compatible(row, schema_version)):
            warning(f'skipping incompatible part: {part_id}')
            continue
        _, last = get_version_range(row)
        if last.major > schema_version.major:
            if not has_mapping(row, schema_version):
                error(f'skipping part with missing version1 fields: {part_id}')
                continue
        result.append(row)
    return result


def gen_partmap(parts: Dataset) -> PartMap:
    {get_partID(part): part for part in parts}


def partmap(parts) -> PartMap:
    return {get_partID(part): part for part in parts}


def map_ids(mappings: Dict[PartId, PartId], part_ids: List[PartId],
            ver: Version) -> List[PartId]:
    if ver.major == 1:
        return flatten([mappings[id] for id in part_ids])
    else:
        return part_ids


def gen_partdata(parts: Dataset, version: Version):
    tables = list(filter(is_table, parts))
    table_ids = list(map(get_partID, tables))
    attributes = list(filter(is_attr, parts))
    categories = list(filter(is_cat, parts))
    catsets = partmap(filter(is_catset_attr, parts))
    bool_set0 = tuple(map(get_partID, islice(filter(is_bool_set, parts), 2)))
    null_set = set(map(get_partID, filter(is_null_set, parts)))

    # Map tables' version1Table to their partID, to be able to find the current
    # table from a v1 reference.
    table_ids_v1_v2 = {}
    for p in tables:
        part_id = get_partID(p)
        ids = _parse_version1Field(p, V1_TABLE)
        for id in ids:
            table_ids_v1_v2[id] = part_id

    table_attrs = defaultdict(list)
    for attr in attributes:
        attr_table_ids = []
        if not is_compatible(attr, ODM_VERSION):
            for id_v1 in _parse_version1Field(attr, V1_TABLE):
                id_v2 = table_ids_v1_v2[id_v1]
                attr_table_ids.append(id_v2)
        else:
            attr_table_ids.append(_get_table_id(attr))
        assert len(attr_table_ids) > 0
        for id in attr_table_ids:
            table_attrs[id].append(attr)

    table_data = {}
    for table in tables:
        table_id = get_partID(table)
        table_data[table_id] = TableData(
            part=table,
            attributes=table_attrs[table_id]
        )

    catset_data = {}
    for attr_id, cs in catsets.items():
        cs_id = cs[CATSET_ID]
        cs_cats = list(filter(lambda p: p[CATSET_ID] == cs_id, categories))
        cs_table_ids = set(filter(lambda tid: cs.get(tid), table_ids))
        values = list(map(get_partID, cs_cats))
        catset_data[attr_id] = CatsetData(
            part=cs,
            cat_parts=cs_cats,
            cat_values=values,
            table_ids=cs_table_ids,
        )

    mappings = {get_partID(p): get_mappings(p, version) for p in parts}
    assert None not in mappings

    bool_set1 = set(map_ids(mappings, list(bool_set0), version))

    # TODO: preserve unmapped version of bool_set for bool meta fields
    return PartData(
        bool_set=bool_set1,
        null_set=null_set,
        table_data=table_data,
        catset_data=catset_data,
        mappings=mappings,
    )
