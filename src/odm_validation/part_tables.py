"""Part-table definitions."""

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import islice
from logging import error, info, warning
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
FIRST_RELEASED = 'firstReleased'
LAST_UPDATED = 'lastUpdated'
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
DEPRECIATED = 'depreciated'  # aka deprecated
MANDATORY = 'mandatory'
MISSINGNESS = 'missingness'
PART_NULL_SET = {'', 'NA', 'Not applicable', 'null'}
TABLES = 'tables'
VARIABLES = 'variables'
VARIABLE_CATEGORIES = 'variableCategories'

V1_VARIABLE = 'version1Variable'
V1_LOCATION = 'version1Location'
V1_TABLE = 'version1Table'
V1_CATEGORY = 'version1Category'


# mapping
V1_KIND_MAP = {
    TABLES: MapKind.TABLE,
    VARIABLES: MapKind.ATTRIBUTE,
    VARIABLE_CATEGORIES: MapKind.CATEGORY,
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


def _strip_prerelease(v: Version) -> Version:
    result = v
    result._prerelease = None
    return result


def get_version_range(part: dict) -> (Version, Version):
    # XXX: must have default for tests (without versioned parts) to work
    row = part
    v1 = Version(major=1)
    latest = _strip_prerelease(ODM_VERSION)
    first = parse_row_version(row, FIRST_RELEASED, default=v1)
    last = parse_row_version(row, LAST_UPDATED, default=latest)
    assert first <= last
    return (first, last)


def is_compatible(part, version: Version) -> bool:
    """Returns True if part is compatible with `version`."""
    # XXX: prerelease (like rc.3, etc.) must be stripped from `version` before
    # compare, because a version with a rc-suffix is seen as less than a
    # version without it, and our ODM version is lagging behind the version of
    # the parts (which don't have suffixes) in that sense, but we still want
    # them to be equal.
    # Example: (ODM version) 2.0.0-rc.3 < (part version) 2.0.0
    v = _strip_prerelease(version)
    first, last = get_version_range(part)
    active = is_active(part)
    return (first <= v and v < last) or (v == last and active)


def should_have_mapping(part_type, first: Version, latest: Version) -> bool:
    # All parts released before the latest (major) version should have a
    # mapping to that previous version, unless it's a 'missingness' part.
    if part_type == MISSINGNESS:
        return
    return first.major < latest.major


def _parse_version1Field(part, key) -> List[str]:
    "`key` must be one of the part columns that starts with 'version1*'."
    val = part.get(key)
    if not val:
        return []
    raw_ids = val.split(';')
    return list(map(str.strip, raw_ids))


def _normalize_key(key: Optional[str]) -> Optional[str]:
    """Returns `key` with the first char in lower case."""
    # TODO: remove this when casing is fixed in the dictionary
    if not key:
        return
    return key[0].lower() + key[1:]


def _get_mappings(part: dict, version: Version) -> Optional[List[PartId]]:
    "Returns the mapping from part.partID to the equivalent ids in `version`."
    # XXX:
    # - parts may be missing version1 fields
    # - partType 'missingness' does not have version1 fields
    # - catSet 'booleanSet' is not required to have a version1Location
    part_type = part.get(PART_TYPE)
    if not should_have_mapping(part_type, version, ODM_VERSION):
        return
    ids = []
    loc = part.get(V1_LOCATION)
    kind = V1_KIND_MAP.get(_normalize_key(loc))
    try:
        if kind == MapKind.TABLE:
            ids = _parse_version1Field(part, V1_TABLE)
        elif kind == MapKind.ATTRIBUTE:
            ids = _parse_version1Field(part, V1_VARIABLE)
        elif kind == MapKind.CATEGORY or is_bool_set(part):
            ids = _parse_version1Field(part, V1_CATEGORY)
    except KeyError:
        return
    valid_ids = list(filter(lambda id: id and id != '', ids))
    if len(valid_ids) == 0:
        return
    return ids


def is_active(part) -> bool:
    "Returns True if the part status is active or missing."
    # missing status defaults to "active" to make it easier to write tests
    status = part.get(STATUS)
    return (not status) or (status == ACTIVE)


def has_mapping(part: dict, version: Version) -> bool:
    ms = _get_mappings(part, version)
    return ms and len(ms) > 0


def table_required_field(table_name):
    return table_name + 'Required'


def get_catset_id(p: Part) -> str:
    # XXX: measureID doesn't have a catSetID due to partType=measure being its
    # implicit catset.
    result = p.get(CATSET_ID)
    if not result and p.get(PART_ID) == 'measureID':
        result = 'measure'
    return result


def has_catset(p):
    return bool(get_catset_id(p))


def is_bool_set(part):
    return get_catset_id(part) == BOOLEAN_SET


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

    1. partID (if partType is table)
    2. <table>Required (addressesRequired, etc.)
    3. <table>=<column_kind> (addresses=header, etc.)
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
    warning(f'missing table relation for part {get_partID(part)}')


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


def filter_compatible(parts: Dataset, version: Version) -> Dataset:
    """Returns `parts` that are compatible with `version`."""
    result = []
    latest = ODM_VERSION
    for row in parts:
        part_id = get_partID(row)
        if not (is_compatible(row, version)):
            info(f'skipping incompatible part: {part_id}')
            continue
        first, _ = get_version_range(row)
        if version.major < latest.major:
            if should_have_mapping(row.get(PART_TYPE), first, latest):
                if not has_mapping(row, version):
                    error(f'skipping part missing version1 fields: {part_id}')
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


def _table_has_attr(table: Part, attr: Part, version: Version):
    # docs/specs/odm-how-tos.md#how-to-get-the-columns-names-for-a-table
    assert is_attr(attr)
    result = get_partID(table) in attr
    if not result and version.major == 1:
        result = (table[V1_TABLE] in _parse_version1Field(attr, V1_TABLE))
    return result


def gen_partdata(parts: Dataset, version: Version):
    all_parts = partmap(parts)
    tables = list(filter(is_table, parts))
    attributes = list(filter(is_attr, parts))
    categories = list(filter(is_cat, parts))
    catsets = partmap(filter(is_catset_attr, parts))
    bool_set0 = tuple(map(get_partID, islice(filter(is_bool_set, parts), 2)))
    null_set = set(map(get_partID, filter(is_null_set, parts)))

    table_data = {}
    for table in tables:
        table_id = get_partID(table)
        attributes = list(
            filter(lambda attr: _table_has_attr(table, attr, version),
                   filter(is_attr, parts)))
        table_data[table_id] = TableData(
            part=table,
            attributes=attributes,
        )

    # v2 catsets
    catset_data: Dict[PartId, CatsetData] = {}
    for attr_id, cs in catsets.items():
        cs_id = get_catset_id(cs)
        cs_cats = list(filter(lambda p: get_catset_id(p) == cs_id, categories))
        values = list(map(get_partID, cs_cats))
        catset_data[attr_id] = CatsetData(
            part=cs,
            cat_parts=cs_cats,
            cat_values=values,
        )

    # v1 catsets
    #
    # - A category in v1 is any part with a value in version1Category (and the
    #   other "version1*" fields). The partType can be anything, and doesn't
    #   have to be "category".
    # - The v1 categories are grouped by `(version1Table, version1Variable)`.
    # - All valid v1 categories are currently associated with a v2 catset
    #   attribute. Those attributes specify which set of categories belong to
    #   them via the version1-table/variable pair.
    #
    # XXX: Some v1 categories (like "tp24s") don't belong to any attributes, so
    # we can only assume that it shouldn't be included in the schema. It seems
    # like this is a trend among the "*Default" category sets.
    if version.major == 1:
        def is_cat_v1(p: Part) -> bool:
            "Returns true if `p` is a v1-only category."
            return (p.get(V1_TABLE) and
                    p.get(V1_LOCATION) == VARIABLE_CATEGORIES and
                    p.get(V1_VARIABLE) and
                    p.get(V1_CATEGORY))

        categories_v1: List[Part] = list(filter(is_cat_v1, parts))

        attr_cats = defaultdict(list)
        for cat in categories_v1:
            cat_tables = set(_parse_version1Field(cat, V1_TABLE))
            cat_vars = set(_parse_version1Field(cat, V1_VARIABLE))

            # find a catset attr that matches
            for attr_id in catset_data:
                attr = all_parts[attr_id]
                attr_tables_v1 = set(_parse_version1Field(attr, V1_TABLE))
                attr_vars_v1 = set(_parse_version1Field(attr, V1_VARIABLE))
                tables_match = len(cat_tables & attr_tables_v1) > 0
                vars_match = len(cat_vars & attr_vars_v1) > 0
                if tables_match and vars_match:
                    attr_cats[attr_id].append(cat)

        for attr_id, cats in attr_cats.items():
            values_v1 = flatten(list(
                map(lambda p: _parse_version1Field(p, V1_CATEGORY), cats)))
            catset_data[attr_id] = CatsetData(
                part=all_parts[attr_id],
                cat_parts=cats,
                cat_values=values_v1
            )

    mappings = {get_partID(p): _get_mappings(p, version) for p in parts}
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
