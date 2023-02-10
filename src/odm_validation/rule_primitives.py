import logging
from dataclasses import dataclass
from logging import warning
from typing import Any, Callable, List, Optional, Set
# from pprint import pprint

import part_tables as pt
from part_tables import Meta, MetaEntry, Part, PartData, PartId
from schemas import init_attr_schema, init_table_schema
from stdext import (
    deep_update,
    parse_datetime,
    try_parse_float,
    try_parse_int,
)
from versions import Version

AttrPredicate = Callable[[pt.TableId, Part], bool]


@dataclass(frozen=True)
class OdmValueCtx:
    """ODM value context."""
    value: str
    datatype: str
    bool_set: pt.BoolSet
    null_set: Set[str]

    @staticmethod
    def default():
        return OdmValueCtx(value=None, datatype=None, bool_set=None,
                           null_set={})


def get_table_meta(table: Part, version: Version) -> Meta:
    keys = [pt.PART_ID, pt.PART_TYPE]
    if version.major == 1:
        keys += [pt.V1_LOCATION, pt.V1_TABLE]
    m: MetaEntry = {k: table[k] for k in keys}
    return [m]


def _get_attr_meta(attr: Part, table_id: PartId, version: Version,
                   odm_key: str = None):
    keys = [pt.PART_ID, table_id, pt.table_required_field(table_id)]
    if version.major == 1:
        keys += [pt.V1_LOCATION, pt.V1_TABLE, pt.V1_VARIABLE]
    if odm_key:
        keys += [odm_key]
    return [{k: attr[k] for k in keys if k in attr}]


def get_catset_meta(table_id: PartId, catset: Part, categories: List[Part],
                    version: Version) -> Meta:
    common_keys = [pt.PART_ID, pt.CATSET_ID]
    catset_keys = common_keys + [table_id, pt.DATA_TYPE]
    cat_keys = common_keys + [pt.PART_TYPE]
    if version.major == 1:
        v1_keys = [pt.V1_LOCATION, pt.V1_TABLE, pt.V1_VARIABLE]
        catset_keys += v1_keys
        cat_keys += v1_keys + [pt.V1_CATEGORY]
    meta: Meta = []
    meta.append({k: catset[k] for k in catset_keys})
    for cat in categories:
        meta.append({k: cat[k] for k in cat_keys})
    return meta


def get_part_ids(parts: List[Part]) -> List[PartId]:
    return list(map(pt.get_partID, parts))


def _get_mapped_part_id(data: PartData, part_id: PartId,
                        version: Version) -> PartId:
    if version.major == 1:
        return data.mappings[part_id][0]
    else:
        return part_id


def table_items(data: PartData, version: Version):
    """Iterates over all tables.

    Yields a tuple of: (original id, mapped id, part).
    """
    for table_id0, td in data.table_data.items():
        table_id1 = _get_mapped_part_id(data, table_id0, version)
        table = td.part
        yield (table_id0, table_id1, table)


def table_items2(data: PartData):
    """Iterates over all table parts from `data`."""
    for _, td in data.table_data.items():
        yield td.part


def catset_items(data: PartData, version: Version):
    """Iterates over all category-set attributes.

    Yields a tuple of: (original id, mapped id, part)."""
    for attr_id0, cs_data in data.catset_data.items():
        attr_id1 = _get_mapped_part_id(data, attr_id0, version)
        yield (attr_id0, attr_id1, cs_data)


def attr_items(data: PartData, table_id: PartId, version: Version):
    """Iterates over all attributes in a table.

    Yields a tuple of: (original id, mapped id, part)."""
    for attr in data.table_data[table_id].attributes:
        attr_id0 = pt.get_partID(attr)
        attr_id1 = _get_mapped_part_id(data, attr_id0, version)
        yield (attr_id0, attr_id1, attr)


def attr_items2(data: PartData, table_id: PartId, key: str):
    """Iterates over all attribute parts with `key`, which is part of table
    `table_id`, from `data`."""
    return filter(lambda part: key in part,
                  data.table_data[table_id].attributes)


def attr_items_pred(data: PartData, table_id: PartId, pred: AttrPredicate):
    """Iterates over all attribute parts of table `table_id` that fulfills
    `pred`."""
    return filter(lambda attr: pred(table_id, attr),
                  data.table_data[table_id].attributes)


def init_table_schema2(schema, data, table, version):
    """This is a helper for creating the table schema, to make it easier to
    write rule-functions. This should be prefered over using
    `init_table_schema` directly."""
    # This is not part of module 'schemas' due to simplicity. It has
    # dependencies in this file and the modules may be merged soon enough.
    table_id0 = pt.get_partID(table)
    table_id1 = _get_mapped_part_id(data, table_id0, version)
    table_meta = get_table_meta(table, version)
    return init_table_schema(table_id1, table_meta, {})


def set_attr_schema(table_schema, data, table, attr, rule_id,
                    odm_key: Optional[str], cerb_rules, version):
    table_id0 = pt.get_partID(table)
    table_id1 = list(table_schema.keys())[0]
    attr_id0 = pt.get_partID(attr)
    attr_id1 = _get_mapped_part_id(data, attr_id0, version)
    attr_meta = _get_attr_meta(attr, table_id0, version, odm_key)
    attr_schema = init_attr_schema(attr_id1, rule_id, cerb_rules, attr_meta)
    deep_update(table_schema[table_id1]['schema']['schema'], attr_schema)


def init_val_ctx(data: PartData, attr: Part, odm_key: Optional[str],
                 ) -> Optional[OdmValueCtx]:
    odm_val = attr.get(odm_key)
    if odm_key and not odm_val:
        warning(f'missing value for {pt.get_partID(attr)}.{odm_key}')
        return
    odm_datatype = attr.get(pt.DATA_TYPE)
    return OdmValueCtx(value=odm_val, datatype=odm_datatype,
                       bool_set=data.bool_set, null_set=data.null_set)


def gen_value_schema(data: pt.PartData, ver: Version, rule_id: str,
                     odm_key: str, gen_cerb_rules):
    """Provides a simple way to generate a value schema. This should be
    prefered to iterating over part-data directly in the rule-functions.

    A value-schema is a schema that maps an ODM-attribute to a cerberus schema
    attribute. Ex: minValue -> min.

    :odm_key: The ODM rule attribute
    :gen_cerb_rules: A function returning a dict of Cerberus rules
    """
    schema = {}
    for table in table_items2(data):
        table_id0 = pt.get_partID(table)
        table_schema = init_table_schema2(schema, data, table, ver)
        for attr in attr_items2(data, table_id0, odm_key):
            val_ctx = init_val_ctx(data, attr, odm_key)
            if not val_ctx:
                continue
            cerb_rules = gen_cerb_rules(val_ctx)
            set_attr_schema(table_schema, data, table, attr, rule_id,
                            odm_key, cerb_rules, ver)
        deep_update(schema, table_schema)
    return schema


def is_mandatory(table_id: pt.TableId, attr: Part):
    # Checks whether an attribute is mandatory in a table
    req_key = pt.table_required_field(table_id)
    req_val = attr.get(req_key)
    return req_val == pt.MANDATORY


def is_primary_key(table_id: pt.TableId, attr: Part):
    return attr.get(table_id) == pt.ColumnKind.PK.value


def gen_conditional_schema(data: pt.PartData, ver: Version, rule_id: str,
                           gen_cerb_rules, pred: AttrPredicate):
    """Helper function to generate a cerberus schema that implements an ODM
    validation rule. Uses `pred` to decide whether an entry should be created
    for an attribute in a table.
    """
    schema = {}
    odm_key = None
    for table in table_items2(data):
        table_id = pt.get_partID(table)
        table_schema = init_table_schema2(schema, data, table, ver)
        for attr in attr_items_pred(data, table_id, pred):
            val_ctx = init_val_ctx(data, attr, odm_key)
            if not val_ctx:
                continue
            cerb_rules = gen_cerb_rules(val_ctx)
            set_attr_schema(table_schema, data, table, attr, rule_id,
                            odm_key, cerb_rules, ver)
        deep_update(schema, table_schema)
    return schema


def _odm_to_cerb_datatype(odm_datatype: str) -> Optional[str]:
    t = odm_datatype
    assert t
    if t in ['boolean', 'categorical', 'varchar']:
        return 'string'
    if t in ['datetime', 'integer', 'float']:
        return t
    logging.error(f'odm datatype {t} is not implemented')


def gen_cerb_rules_for_type(val_ctx: OdmValueCtx):
    odm_type = val_ctx.datatype
    cerb_type = _odm_to_cerb_datatype(odm_type) if odm_type else None
    result = {'type': cerb_type}
    if cerb_type != 'string':
        result['coerce'] = cerb_type
    if odm_type == 'boolean':
        result['allowed'] = sorted(val_ctx.bool_set)
    return result


def parse_odm_val(val_ctx: OdmValueCtx) -> Optional[Any]:
    """Parses the ODM value from `val_ctx`."""
    val = val_ctx.value
    kind = val_ctx.datatype
    if not val:
        return
    if kind == 'integer':
        return try_parse_int(val)
    elif kind == 'float':
        return try_parse_float(val)
    elif kind == 'datetime':
        return parse_datetime(val)
    elif kind == 'varchar':
        return str(val)
    else:
        assert False, f'{kind} parsing not impl.'
