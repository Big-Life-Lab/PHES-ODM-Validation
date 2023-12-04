"""Part-table definitions."""

import inspect
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from logging import error, info, warning
from os.path import join
from pathlib import Path
from semver import Version
from typing import DefaultDict, Dict, List, Optional, Set, Tuple
# from pprint import pprint

from stdext import flatten
from versions import parse_version


# type aliases (primitive)
Part = dict
PartId = str
Row = dict
SetId = str

AttrId = PartId
TableId = PartId

# type aliases (meta)
MetaEntry = Dict[str, str]
Meta = List[MetaEntry]
MetaMap = DefaultDict[PartId, Meta]

# type aliases (other)
Dataset = List[Row]
PartMap = Dict[PartId, Part]
TableAttrId = Tuple[TableId, AttrId]


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
class OdmData:
    "Data generated from the 'parts' and 'sets' tables."

    # how are categories used?
    # v2: for each table -> for each attr -> for each cat in mmaSet
    # v1: for each table's v1 table -> for each attr w/ v1loc=var and eq v1 tbl
    #         if version1Location==variableCategories then get "setID_v1" from
    #           version1Variable, and set values from version1Category
    #         else use version1Variable directly

    bool_set: Set[str]
    null_set: Set[str]
    catset_data: Dict[TableAttrId, CatsetData]
    table_data: Dict[PartId, TableData]  # table data, by table id
    mappings: Dict[PartId, List[PartId]]  # v1 mapping, by part id


def _get_asset_dir() -> str:
    """returns a list of odm-validation schema file paths"""
    mod = sys.modules[__name__]
    mod_path = inspect.getfile(mod)
    mod_dir = os.path.dirname(mod_path)
    asset_dir = os.path.join(mod_dir, 'assets')

    # If the `asset_dir` path doesn't exist, then we can assume that the
    # package hasn't been installed, but is used directly in a development
    # environment, meaning that we need to specify the path as it is in the
    # repo.
    if not os.path.isdir(asset_dir):
        asset_dir = os.path.join(mod_dir, '..', '..', 'assets')

    return asset_dir


def _get_latest_odm_version_str() -> str:
    asset_dir = _get_asset_dir()
    schema_dir = join(asset_dir, 'validation-schemas')
    versions = []
    for schema_path in Path(schema_dir).glob('schema-v*'):
        schema_name = os.path.basename(schema_path)
        if not (match := re.search('v(.+)', schema_name)):
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
CATSET_ID = 'mmaSet'
DATA_TYPE = 'dataType'
FIRST_RELEASED = 'firstReleased'
LAST_UPDATED = 'lastUpdated'
PART_ID = 'partID'
PART_TYPE = 'partType'
SET_ID = 'setID'
STATUS = 'status'

PART_ID_ORIGINAL = 'partID_original'
TABLE_ID_ORIGINAL = 'tableID_original'
TABLE_REQUIRED_ORIGINAL = 'tableRequired_original'

# suffixes
_REQUIRED = 'Required'

# partType constants
ATTRIBUTE = 'attributes'
CATEGORY = 'categories'
TABLE = 'tables'

# other value constants
ACTIVE = 'active'
BOOLEAN = 'boolean'
BOOLEAN_SET = 'booleanSet'
DATETIME = 'datetime'
DEPRECIATED = 'depreciated'  # aka deprecated
MANDATORY = 'mandatory'
MEASURE_ID = 'measure'
MISSINGNESS = 'missingness'
PART_NULL_SET = {'', 'NA', 'Not applicable', 'null'}
TABLES = 'tables'
VARIABLES = 'variables'
VARIABLE_CATEGORIES = 'variableCategories'

V1_VARIABLE = 'version1Variable'
V1_LOCATION = 'version1Location'
V1_TABLE = 'version1Table'
V1_CATEGORY = 'version1Category'

# XXX: These are the part ids for the boolean set parts. They are hardcoded
# here to be able to check if a part is in the boolean set. This is only needed
# to reduce complexity when checking that a part has the required
# version1-fields, which the boolean-set parts do not.
BOOL_SET = {'true', 'false'}

# mapping
V1_KIND_MAP = {
    TABLES: MapKind.TABLE,
    VARIABLES: MapKind.ATTRIBUTE,
    VARIABLE_CATEGORIES: MapKind.CATEGORY,
}


def get_validation_rule_fields(column_meta, rule_ids: List[str]):
    # TODO: add meta from sets-table?
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


def should_have_mapping(part, first: Version, latest: Version) -> bool:
    # All parts released before the latest (major) version should have a
    # mapping to that previous version, unless it's a 'missingness' part.
    if (part.get(PART_TYPE) == MISSINGNESS):
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
    if not should_have_mapping(part, version, ODM_VERSION):
        return
    ids = []
    loc = part.get(V1_LOCATION)
    kind = V1_KIND_MAP.get(_normalize_key(loc))
    try:
        if kind == MapKind.TABLE:
            ids = _parse_version1Field(part, V1_TABLE)
        elif kind == MapKind.ATTRIBUTE:
            ids = _parse_version1Field(part, V1_VARIABLE)
        elif kind == MapKind.CATEGORY or part.get(PART_ID) in BOOL_SET:
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
    # XXX: This is not called `get_set_id` because it depends on `mmaSet` which
    # supposedly is different from `setID`.
    # XXX: measureID doesn't have a set id due to partType=measure being its
    # implicit set.
    result = p.get(CATSET_ID)
    if not result and p.get(PART_ID) == MEASURE_ID:
        result = MEASURE_ID
    return result


def has_catset(p):
    return bool(get_catset_id(p))


def is_null_set(part):
    # the ODM doesn't have these values as a catset, but it's a set
    return part.get(PART_TYPE) == MISSINGNESS


def is_table(p):
    return p.get(PART_TYPE) == TABLE


def is_attr(p):
    return p.get(PART_TYPE) == ATTRIBUTE


def is_catset_attr(p):
    "A category set attribute holds a category value from the specified set."
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


def filter_compatible(rows: Dataset, version: Version) -> Dataset:
    "Returns the subset of `rows` that are compatible with `version`."
    result = []
    for row in rows:
        if not (is_compatible(row, version)):
            info(f'skipping incompatible part: {get_partID(row)}')
            continue
        result.append(row)
    return result


def filter_backportable(parts: Dataset, version: Version) -> Dataset:
    "Retuns the subset of `parts` that has a mapping to v1."
    result = []
    latest = ODM_VERSION
    for row in parts:
        part_id = get_partID(row)
        first, _ = get_version_range(row)
        if version.major < latest.major:
            if should_have_mapping(row, first, latest):
                if not has_mapping(row, version):
                    error(f'skipping part missing version1 fields: {part_id}')
                    continue
        result.append(row)
    return result


def gen_partmap(parts) -> PartMap:
    "Returns a mapping/dict between part-id and part."
    return {get_partID(part): part for part in parts}


def map_ids(mappings: Dict[PartId, PartId], part_ids: List[PartId],
            ver: Version) -> List[PartId]:
    "Maps `part_ids` using `mappings`. Defaults to original id."
    # XXX: The default fallback of `mappings.get` is needed in tests that don't
    # have the boolean parts in their parts list.
    if ver.major == 1:
        return flatten([mappings.get(id, id) for id in part_ids])
    else:
        return part_ids


def _table_has_attr(table: Part, attr: Part, version: Version) -> bool:
    # docs/specs/odm-how-tos.md#how-to-get-the-columns-names-for-a-table
    assert is_attr(attr)
    if version.major == 1:
        table_ids = set(_parse_version1Field(table, V1_TABLE))
        attr_table_ids = set(_parse_version1Field(attr, V1_TABLE))
        return len(table_ids & attr_table_ids) > 0
    else:
        return get_partID(table) in attr


def validate_and_fix(all_parts: PartMap, version):
    # function parts/sets validation and hotfixes

    # FIXME: true/false parts are missing version1Category
    for part_id in BOOL_SET:
        part = all_parts.get(part_id)
        if part and should_have_mapping(part, version, ODM_VERSION):
            if V1_CATEGORY not in part:
                part[V1_CATEGORY] = part_id.capitalize()
                assert has_mapping(part, version)


def gen_odmdata(parts: Dataset, sets: Dataset, version: Version):
    # `parts` must be stripped first, before further processing. This is
    # important for performance and simplicity of implementation.

    # process parts
    parts = strip(parts)
    all_parts = gen_partmap(parts)
    validate_and_fix(all_parts, version)
    parts = filter_compatible(parts, version)
    parts = filter_backportable(parts, version)

    # process sets
    sets = filter_compatible(sets, version)

    tables = gen_partmap(filter(is_table, parts))
    attributes = list(filter(is_attr, parts))
    null_set = set(map(get_partID, filter(is_null_set, parts)))

    # bool set
    bool_set0 = {}
    bool_set_rows = []
    if version.major == 1:
        if version.minor > 0:
            bool_set0 = BOOL_SET
    else:
        bool_set_rows = list(filter(lambda s: s[SET_ID] == BOOLEAN_SET, sets))
        bool_set0 = set(map(get_partID, bool_set_rows))

    # table attributes
    table_data = {}
    for table_id, table in tables.items():
        table_attributes = list(
            filter(lambda attr: _table_has_attr(table, attr, version),
                   attributes))
        table_data[table_id] = TableData(
            part=table,
            attributes=gen_partmap(table_attributes),
        )

    # category sets
    # v1: Set ids are not unique and must be paired with the table id.
    #     Ex: the `type` cat set in v1 differs depending on the table.
    # v2: Set ids are unique and formalised as "mmaSet/setID".
    catset_data: Dict[TableAttrId, CatsetData] = {}
    if version.major == 1:
        def is_cat_v1(p: Part) -> bool:
            return (p.get(V1_TABLE) and
                    p.get(V1_LOCATION) == VARIABLE_CATEGORIES and
                    p.get(V1_VARIABLE) and
                    p.get(V1_CATEGORY))

        def attr_has_cat_v1(table_id_v1, attr, cat):
            """Returns true if `cat` is in the category set of `attr`, in table
            `table_id_v1`"""
            return (cat[V1_VARIABLE] == attr[V1_VARIABLE] and
                    table_id_v1 in _parse_version1Field(cat, V1_TABLE))

        def get_categories_v1(table_id_v1, attr):
            return list(
                filter(lambda c: attr_has_cat_v1(table_id_v1, attr, c),
                       categories_v1))

        categories_v1 = list(filter(is_cat_v1, parts))
        for table_id, table in tables.items():
            table_id_v1 = table[V1_TABLE]
            for attr_id, attr in table_data[table_id].attributes.items():
                cats = get_categories_v1(table_id_v1, attr)
                values = list(map(get_partID, cats))
                data = CatsetData(
                    part=attr,
                    cat_parts=cats,
                    cat_values=values,
                )
                catset_data[(table_id, attr_id)] = data

    else:
        categorical_attrs = gen_partmap(filter(is_catset_attr, parts))
        for attr_id, categorical_attr in categorical_attrs.items():
            set_id = get_catset_id(categorical_attr)
            cs_sets = list(filter(lambda s: s[SET_ID] == set_id, sets))
            cs_cats = list(map(lambda s: all_parts[s[PART_ID]], cs_sets))
            values = list(map(get_partID, cs_cats))
            data = CatsetData(
                part=categorical_attr,
                cat_parts=cs_cats,
                cat_values=values,
            )
            for table_id in tables.keys():
                catset_data[(table_id, attr_id)] = data

    mappings = {get_partID(p): _get_mappings(p, version) for p in parts}
    assert None not in mappings

    bool_set1 = set(map_ids(mappings, list(bool_set0), version))

    # TODO: preserve unmapped version of bool_set for bool meta fields
    return OdmData(
        bool_set=bool_set1,
        null_set=null_set,
        table_data=table_data,
        catset_data=catset_data,
        mappings=mappings,
    )
