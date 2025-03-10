"""Part-table definitions."""
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import partial
from logging import error, info
from semver import Version
from typing import Optional, Union, cast
# from pprint import pprint

import odm_validation.odm as odm
from odm_validation.stdext import flatten
from odm_validation.versions import parse_version


# type aliases (primitive)
Part = dict
PartId = str
Row = dict
SetId = str

AttrId = PartId
TableId = PartId

# type aliases (meta)
MetaEntry = dict[str, str]  # per partID
Meta = list[MetaEntry]  # per ruleID
ColRuleMeta = dict[str, Union[Meta, str]]  # {'meta': Meta, 'ruleID': str}
ColMeta = list[ColRuleMeta]

# type aliases (other)
Dataset = list[Row]
PartMap = dict[PartId, Part]
SomeValue = Union[int, float, str, datetime]
TableAttrId = tuple[TableId, AttrId]


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
    cat_parts: list[Part]  # the parts belonging to this catset
    cat_values: list[str]  # Ex: category set `coll` has ['flowPr', ...]


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

    bool_set: set[str]
    null_set: set[str]
    catset_data: dict[TableAttrId, CatsetData]
    table_data: dict[PartId, TableData]  # table data, by table id
    mappings: dict[PartId, list[PartId]]  # v1 mapping, by part id


UNITTEST = ('unittest' in sys.modules)

# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

COLUMN_KINDS = set(list(map(lambda e: e.value, ColumnKind)))

# field constants
CATSET_ID = 'mmaSet'
CLASS = 'class'
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
BOOL_PART_IDS = ['FALSE', 'TRUE']
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

# mapping
V1_KIND_MAP = {
    TABLES: MapKind.TABLE,
    VARIABLES: MapKind.ATTRIBUTE,
    VARIABLE_CATEGORIES: MapKind.CATEGORY,
}


def get_validation_rule_fields(column_meta: ColMeta, rule_ids: list[str]
                               ) -> Meta:
    # TODO: add meta from sets-table?
    if not column_meta:
        return []
    assert isinstance(column_meta, list)
    assert isinstance(column_meta[0], dict)
    assert isinstance(column_meta[0].get('meta', []), list)
    return flatten(list(
        map(lambda x: cast(Meta, x.get('meta', [])),
            filter(lambda x: x['ruleID'] in rule_ids,
                   column_meta))))


def parse_row_version(row: dict, field: str, default: Optional[Version] = None
                      ) -> Version:
    return parse_version(row.get(field), get_partID(row), field, default)


def get_initial_version(part: Part) -> Version:
    v1 = Version(major=1)
    return parse_row_version(part, FIRST_RELEASED, default=v1)


def is_compatible(part: Part, version: Version) -> bool:
    '''Returns True if `part` is compatible with `version`.'''
    # The version range for a part is [firstReleased, currentVersion], unless
    # it's not active anymore, then it becomes [firstReleased, lastUpdated>.
    #
    # XXX: must have a default value for tests without versioned parts to work
    v = version
    first = get_initial_version(part)
    latest = odm.VERSION
    assert v <= latest
    if is_active(part):
        assert first <= latest
        return first <= v
    else:
        last = parse_row_version(part, LAST_UPDATED, default=latest)
        assert first <= last
        return first <= v < last


def should_have_mapping(part: Part, first: Version, latest: Version) -> bool:
    # All parts released before the latest (major) version should have a
    # mapping to that previous version, unless it's a 'missingness' part.
    if (part.get(PART_TYPE) == MISSINGNESS):
        return False
    return first.major < latest.major


def _parse_version1Field(part: Part, key: str) -> list[str]:
    "`key` must be one of the part columns that starts with 'version1*'."
    val = part.get(key)
    if not val:
        return []
    raw_ids = val.split(';')
    return list(map(str.strip, raw_ids))


def _normalize_key(key: Optional[str]) -> str:
    """Returns `key` with the first char in lower case."""
    # TODO: remove this when casing is fixed in the dictionary
    if not key:
        return ''
    return key[0].lower() + key[1:]


def _get_mappings(part: dict, version: Version) -> list[PartId]:
    "Returns the mapping from part.partID to the equivalent ids in `version`."
    # XXX:
    # - parts may be missing version1 fields
    # - partType 'missingness' does not have version1 fields
    # - catSet 'booleanSet' is not required to have a version1Location
    if not should_have_mapping(part, version, odm.VERSION):
        return []
    ids = []
    loc = part.get(V1_LOCATION)
    kind = V1_KIND_MAP.get(_normalize_key(loc))
    try:
        if kind == MapKind.TABLE:
            ids = _parse_version1Field(part, V1_TABLE)
        elif kind == MapKind.ATTRIBUTE:
            ids = _parse_version1Field(part, V1_VARIABLE)
        elif kind == MapKind.CATEGORY or part.get(PART_ID) in BOOL_PART_IDS:
            ids = _parse_version1Field(part, V1_CATEGORY)
    except KeyError:
        return []
    valid_ids = list(filter(lambda id: id and id != '', ids))
    if len(valid_ids) == 0:
        return []
    return ids


def is_active(part: Part) -> bool:
    "Returns True if the part status is active or missing."
    # missing status defaults to "active" to make it easier to write tests
    status = part.get(STATUS)
    return (not status) or (status == ACTIVE)


def has_mapping(part: dict, version: Version) -> bool:
    return bool(_get_mappings(part, version))


def table_required_field(table_name: str) -> str:
    return table_name + 'Required'


def get_catset_id(p: Part) -> Optional[str]:
    # XXX: This is not called `get_set_id` because it depends on `mmaSet` which
    # supposedly is different from `setID`.
    # XXX: measureID doesn't have a set id due to partType=measure being its
    # implicit set.
    result = p.get(CATSET_ID)
    if not result and p.get(PART_ID) == MEASURE_ID:
        result = MEASURE_ID
    return result


def has_catset(p: Part) -> bool:
    return bool(get_catset_id(p))


def is_null_set(p: Part) -> bool:
    # the ODM doesn't have these values as a catset, but it's a set
    return p.get(PART_TYPE) == MISSINGNESS


def is_table_v1(p: Part) -> bool:
    return p.get(PART_TYPE) == TABLE


def is_table_v2(p: Part) -> bool:
    # XXX: v2 includes the meta-tables 'parts' and 'sets', which shouldn't be
    # validated
    return is_table_v1(p) and p.get(CLASS) != 'lookup'


def is_attr(p: Part) -> bool:
    return p.get(PART_TYPE) == ATTRIBUTE


def is_catset_attr(p: Part) -> bool:
    "A category set attribute holds a category value from the specified set."
    return is_attr(p) and has_catset(p)


def get_partID(p: Part) -> PartId:
    # TODO: rename to get_partid or get_id?
    return p[PART_ID]


def get_catset_table_ids(row: Row, table_ids: list[str]) -> list[str]:
    result = []
    for table in table_ids:
        if row.get(table):
            result.append(table)
    return result


def _not_empty(kv_pair: tuple) -> bool:
    _, val = kv_pair
    return val not in PART_NULL_SET


def strip(parts: Dataset) -> Dataset:
    """Removes null fields, except from partID."""
    # 'partID' may be defining null fields for data, so we can't strip those.
    # TODO: Strip version1* fields when not version 1.
    result: Dataset = []
    for sparse_row in parts:
        kv_pairs = iter(sparse_row.items())
        (part_id_key, part_id_val) = next(kv_pairs)
        assert part_id_key == PART_ID, 'partID must be the first column'
        row = {k: v for k, v in filter(_not_empty, kv_pairs)}
        row[PART_ID] = part_id_val
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
    latest = odm.VERSION
    for row in parts:
        part_id = get_partID(row)
        first = get_initial_version(row)
        if version.major < latest.major:
            if should_have_mapping(row, first, latest):
                if not has_mapping(row, version):
                    error(f'skipping part missing version1 fields: {part_id}')
                    continue
        result.append(row)
    return result


def gen_partmap(parts: list[Part]) -> PartMap:
    '''maps part-ids to parts'''
    return {get_partID(part): part for part in parts}


def map_ids(mappings: dict[PartId, list[PartId]], part_ids: list[PartId],
            ver: Version) -> list[PartId]:
    "Maps `part_ids` using `mappings`. Defaults to original id."
    # XXX: The default fallback of `mappings.get` is needed in tests that don't
    # have the boolean parts in their parts list.
    if ver.major == 1:
        return flatten([mappings.get(id, [id]) for id in part_ids])
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


def fix_parts(all_parts: PartMap, version: Version) -> None:
    '''fix inconsistencies in the parts'''
    # NOTE: when running tests, parts may not exist, and test data may not be
    # for the specified version

    if (version.major == 2 and version.minor == 0) or UNITTEST:
        # XXX: normalize bool part ids to upper case, since they're lower-case
        # in ODM v2.0
        for upper_id in BOOL_PART_IDS:
            lower_id = upper_id.lower()
            p = all_parts.pop(lower_id, None)
            if p:
                p[PART_ID] = upper_id
                all_parts[upper_id] = p

    if version.major == 2 and version.minor == 0:
        # boolean parts are missing version1Category
        # NOTE: v1 schemas are only generated from ODM v2.0
        for part_id in BOOL_PART_IDS:
            part = all_parts.get(part_id)
            if part and should_have_mapping(part, version, odm.VERSION):
                if V1_CATEGORY not in part:
                    part[V1_CATEGORY] = part_id.capitalize()
                    assert has_mapping(part, version)


def fix_sets(sets: Dataset, version: Version) -> None:
    '''fix inconsistencies in the sets'''
    # XXX: when running tests, parts may not exist

    if version.major == 2:
        if version.minor in [0, 2]:
            # XXX: normalize bool sets' part id to upper case, since they're
            # lower-case in ODM v2.0 and v2.2.
            for s in sets:
                if s[SET_ID] == BOOLEAN_SET:
                    s[PART_ID] = s[PART_ID].upper()

        if version.minor == 2 and version.patch == 3:
            # TODO: remove this if ODM v2.2 gets patched again
            # 'setCompID' has the wrong version (2.3.0) in ODM v2.2.3
            for s in sets:
                if s.get('setCompID') == 'siteTypeSet_triturator':
                    s['firstReleased'] = '2.2.3'
                    s['lastUpdated'] = '2.2.3'


def gen_odmdata(parts: Dataset, sets: Dataset, version: Version) -> OdmData:
    # `parts` must be stripped first, before further processing. This is
    # important for performance and simplicity of implementation.

    # process parts
    parts = strip(parts)
    all_parts = gen_partmap(parts)
    fix_parts(all_parts, version)
    parts = filter_compatible(parts, version)
    parts = filter_backportable(parts, version)

    # process sets
    fix_sets(sets, version)
    sets = filter_compatible(sets, version)

    table_pred = is_table_v1 if version.major < 2 else is_table_v2
    tables = gen_partmap(list(filter(table_pred, parts)))
    attributes = list(filter(is_attr, parts))
    null_set = set(map(get_partID, filter(is_null_set, parts)))

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
    # v1: set ids are not unique and must be paired with the table id.
    #     Ex: the `type` cat set in v1 differs depending on the table.
    # v2: set ids are unique and formalised as "mmaSet/setID".
    catset_data: dict[TableAttrId, CatsetData] = {}
    if version.major == 1:
        def is_cat_v1(p: Part) -> bool:
            return (bool(p.get(V1_TABLE)) and
                    p.get(V1_LOCATION) == VARIABLE_CATEGORIES and
                    bool(p.get(V1_VARIABLE)) and
                    bool(p.get(V1_CATEGORY)))

        def attr_has_cat_v1(table_id_v1: TableId, attr: Part, cat: Part
                            ) -> bool:
            """Returns true if `cat` is in the category set of `attr`, in table
            `table_id_v1`"""
            return (cat[V1_VARIABLE] == attr[V1_VARIABLE] and
                    table_id_v1 in _parse_version1Field(cat, V1_TABLE))

        def get_categories_v1(categories_v1: list[Part], table_id_v1: TableId,
                              attr: Part) -> list[Part]:
            '''returns all v1 category-parts belonging to `attr`'''
            pred = partial(attr_has_cat_v1, table_id_v1, attr)
            return list(filter(pred, categories_v1))

        categories_v1: list[Part] = list(filter(is_cat_v1, parts))
        for table_id, table in tables.items():
            table_id_v1 = table[V1_TABLE]
            for attr_id, attr in table_data[table_id].attributes.items():
                cats = get_categories_v1(categories_v1, table_id_v1, attr)
                values = list(map(get_partID, cats))
                data = CatsetData(
                    part=attr,
                    cat_parts=cats,
                    cat_values=values,
                )
                catset_data[(table_id, attr_id)] = data

    else:
        categorical_attrs = gen_partmap(list(filter(is_catset_attr, parts)))
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

    # TODO: preserve unmapped version of bool_set for bool meta fields
    #
    # NOTE: bool values must be upper case, and the bool part ids are already
    # upper case so we can use them directly
    return OdmData(
        bool_set=set(BOOL_PART_IDS),
        null_set=null_set,
        table_data=table_data,
        catset_data=catset_data,
        mappings=mappings,
    )
