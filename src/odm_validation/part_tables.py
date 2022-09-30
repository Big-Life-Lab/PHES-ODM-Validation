"""Part-table definitions."""

from dataclasses import dataclass
from logging import debug, error
from semver import Version
from typing import Dict, List, Set

import utils
from versions import is_compatible


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


# The following constants are not enums because they would be a pain to use.
# even with a `__str__` overload to avoid writing `.value` all the time,
# we would still have to explicitly call the `str` function.
# Ex: str(PartType.ATTRIBUTE.value) vs ATTRIBUTE

# field constants
CATSET_ID = 'catSetID'
PART_ID = 'partID'
PART_TYPE = 'partType'

# partType constants
ATTRIBUTE = 'attribute'
CATEGORY = 'category'
TABLE = 'table'

# other value constants
MANDATORY = 'Mandatory'
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


def strip(parts: Dataset, version: Version):
    """Removes NA fields and filters by `version`."""
    result = []
    for row in parts:
        if not is_compatible(row, version):
            debug(f'skipping incompatible part: {get_partID(row)}')
            continue
        result.append({k: v for k, v in row.items() if v not in NA})
    return result


V1_FIELD_PREFIX = 'version1'


def _get_part_table_id(part: dict) -> str:
    req = list(filter(lambda k: k.endswith('Required'), part.keys()))[0]
    return req[:req.find('Required')]


# print(_get_part_table_id({'addressesRequired': 'mandatory'}))
# quit()


def replace_id(p: dict, new_id: str) -> dict:
    p['partID'] = new_id


def replace_table(p: dict, table_v2: str, table_v1: str) -> dict:
    p[table_v1] = p.pop(table_v2)
    p[table_required_field(table_v1)] = p.pop(table_required_field(table_v2))


def transform_v2_to_v1(parts: Dataset) -> Dataset:
    """Transforms v2 parts to v1, based on `version1*` fields.

    Should be called after `strip`.
    """
    result = []
    for p0 in parts:
        id_v1 = p0.get('version1Variable')
        kind_v1 = p0.get('version1Location')
        table_v1 = p0.get('version1Table')

        all_v1 = kind_v1 and table_v1 and id_v1
        any_v1 = kind_v1 or table_v1 or id_v1
        if not all_v1:
            if any_v1:
                id = get_partID(p0)
                error(f'missing some `version1*` fields in part {id}')
            p1 = p0
            continue

        # TODO
        if kind_v1 != 'variable':
            error(f'version1Location "{kind_v1}" is not implemented yet')
            p1 = p0
            continue

        p1 = p0.copy()
        table_v2 = _get_part_table_id(p0)
        replace_id(p1, id_v1)
        replace_table(p1, table_v2, table_v1)

        result.append(p1)
    return result


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


def gen_partdata(parts: Dataset, version: Version) -> PartData:
    # `parts` are assumed to be from ODM v2.
    # `parts` are stripped before processing. This is important for performance
    # and simplicity of implementation.
    parts = strip(parts, version)
    if version.major == 1:
        parts = transform_v2_to_v1(parts)

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

    return PartData(
        all_parts=parts,
        attributes=attributes,
        catset_data=catset_data,
        table_data=table_data,
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
                    'meta': [{PART_ID: attr_id}] + meta,
                }
            ]
        }
    }


def update_schema(schema, table_id, attr_id, rule_id, cerb_rule, meta):
    attr_schema = init_attr_schema(attr_id, rule_id, cerb_rule, meta)
    table_schema = init_table_schema(table_id, attr_schema)
    utils.deep_update(table_schema, schema)
