"""Part-table definitions."""

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from itertools import groupby, islice
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
    active = get_part_active(part)
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
    if not key:
        return
    return key[0].lower() + key[1:]


def _get_mappings(part: dict, version: Version) -> Optional[List[PartId]]:
    """Returns a list of part ids from `version` corresponding to `part`,
    or None if there is no mapping.

    :param version: the schema version
    """
    # XXX: Parts may be missing version1 fields.
    # XXX: partType 'missingness' does not have version1 fields.
    # XXX: catSet 'booleanSet' is not required to have a version1Location.
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


def get_part_active(part) -> bool:
    return part.get(STATUS) == ACTIVE


def has_mapping(part: dict, version: Version) -> bool:
    ms = _get_mappings(part, version)
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


def _get_catset_id_v1(p: Part) -> str:
    result = p.get(V1_VARIABLE)
    if not result:
        error(f'missing Version1Variable in {get_partID(p)}')
    return result or 'missingVersion1Variable'


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
    categories = list(filter(is_cat, parts))
    catsets = partmap(filter(is_catset_attr, parts))
    bool_set0 = tuple(map(get_partID, islice(filter(is_bool_set, parts), 2)))
    null_set = set(map(get_partID, filter(is_null_set, parts)))

    def _is_cat_v1(p: Part) -> bool:
        # v1-only, without catSetId
        return (p.get(V1_TABLE) and
                p.get(V1_LOCATION) == 'variableCategories' and
                p.get(V1_CATEGORY) and
                not p.get(CATSET_ID))

    # catsets that are only in v1
    categories_v1: List[Part]
    catset_categories_v1: Dict[PartId, List[Part]]
    if version.major == 1:
        categories_v1 = \
            sorted(filter(_is_cat_v1, parts), key=_get_catset_id_v1)
        catset_categories_v1 = \
            {k: list(g) for k, g in groupby(categories_v1,
                                            key=_get_catset_id_v1)}

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
    # XXX: Some v2 catsets only have v1 categories without catSetId, they
    # should not be included here. They can be identitifed by the lack of
    # (v2) categories/values coming from the catSetId lookup.
    catset_data = {}
    for attr_id, cs in catsets.items():
        cs_id = cs[CATSET_ID]
        cs_cats = list(filter(lambda p: p[CATSET_ID] == cs_id, categories))
        if len(cs_cats) == 0:
            continue
        values = list(map(get_partID, cs_cats))
        catset_data[attr_id] = CatsetData(
            part=cs,
            cat_parts=cs_cats,
            cat_values=values,
        )

    # v1 pseudo-catsets
    # - v1 categories comprise a v1 catset
    # - each category has a value
    # - a catset may be used in multiple tables
    if version.major == 1:
        def _is_catset_v1(p):
            return (p.get(V1_TABLE) and
                    p.get(V1_LOCATION) == 'variables' and
                    p.get(V1_VARIABLE) and
                    not p.get(V1_CATEGORY))

        tablepartv1_partv2 = {(p[V1_TABLE], p[V1_VARIABLE]): p[PART_ID]
                              for p in filter(_is_catset_v1, parts)}
        for attr_id_v1, categories in catset_categories_v1.items():
            values = list(map(lambda p: p.get(V1_CATEGORY), categories))
            table_ids_v1 = list(set(flatten(
                map(lambda p: _parse_version1Field(p, V1_TABLE), categories))))
            for table_id_v1 in table_ids_v1:
                key_v1 = (table_id_v1, attr_id_v1)
                attr_id_v2 = tablepartv1_partv2.get(key_v1)
                if not attr_id_v2:
                    warning(f'missing category mapping for {key_v1}')
                    continue
                part = all_parts[attr_id_v2]
                catset_data[attr_id_v2] = CatsetData(
                    part=part,
                    cat_parts=categories,
                    cat_values=values,
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
