"""Part-table definitions."""

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from logging import error, warning
from semver import Version
from typing import DefaultDict, Dict, List, Optional, Set

from stdext import flatten
from versions import parse_version


# type aliases
PartId = str
Row = dict
Dataset = List[Row]
MetaEntry = Dict[str, str]
Meta = List[MetaEntry]
MetaMap = DefaultDict[PartId, Meta]
Part = dict
PartMap = Dict[PartId, Part]


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
    catset_data: Dict[PartId, CatsetData]  # category-set data, by catset id
    table_data: Dict[PartId, TableData]  # table data, by table id
    mappings: Dict[PartId, List[PartId]]  # v1 mapping, by part id


# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

COLUMN_KINDS = set(list(map(lambda e: e.value, ColumnKind)))

# field constants
CATSET_ID = 'catSetID'
DATA_TYPE = 'dataType'
PART_ID = 'partID'
PART_TYPE = 'partType'

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
MANDATORY = 'mandatory'
NA = {'', 'NA', 'Not applicable'}

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


def parse_version1Category(s: str) -> List[str]:
    cats = s.split(';')
    return list(map(str.strip, cats))


def get_mappings(part: dict, version: Version) -> Optional[List[PartId]]:
    """Returns a list of part ids from `version` corresponding to `part`,
    or None if there is no mapping."""
    if version.major != 1:
        return
    ids = []
    try:
        loc = part[V1_LOCATION]
        kind = V1_KIND_MAP[loc]
        if kind == MapKind.TABLE:
            ids = [part[V1_TABLE]]
        elif kind == MapKind.ATTRIBUTE:
            ids = [part[V1_VARIABLE]]
        elif kind == MapKind.CATEGORY:
            ids = parse_version1Category(part[V1_CATEGORY])
    except KeyError:
        return
    if len(ids) == 0 or None in ids or '' in ids:
        return
    return ids


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
    # TODO: rename to get_partid or get_id?
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


def get_table_id(part: dict) -> Optional[str]:
    """ Retrieves the table id of `part`.

    The value is looked up in the following order:

    1. partID & partType
    2. <table>Required
    3. <table>:<column_kind>

    :raises Exception: when table info is missing.
    """
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


def strip(parts: Dataset):
    # TODO: strip version1* fields when not version 1
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
        part_id = get_partID(row)
        if not (is_compatible(row, version)):
            warning(f'skipping incompatible part: {part_id}')
            continue
        if version.major == 1 and not has_mapping(row, version):
            error(f'skipping part with missing version1 fields: {part_id}')
            continue
        result.append(row)
    return result


def gen_partmap(parts: Dataset) -> PartMap:
    {get_partID(part): part for part in parts}


def partmap(parts) -> PartMap:
    return {get_partID(part): part for part in parts}


def gen_partdata(parts_v2: Dataset, version: Version):
    tables = list(filter(is_table, parts_v2))
    table_ids = list(map(get_partID, tables))
    attributes = list(filter(is_attr, parts_v2))
    categories = list(filter(is_cat, parts_v2))
    catsets = partmap(filter(is_catset_attr, parts_v2))

    table_attrs = defaultdict(list)
    for attr in attributes:
        table_id = get_table_id(attr)
        if table_id:
            table_attrs[table_id].append(attr)

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

    mappings = {get_partID(p): get_mappings(p, version) for p in parts_v2}
    assert None not in mappings

    return PartData(
        table_data=table_data,
        catset_data=catset_data,
        mappings=mappings,
    )
