from typing import Dict, List
# from pprint import pprint

import part_tables as pt
from part_tables import Meta, MetaEntry, Part, PartData, PartId
from schemas import init_attr_schema, init_table_schema, parse_odm_datatype
from stdext import deep_update, flatten
from versions import Version


def get_table_meta(table: Part, version: Version) -> Meta:
    keys = [pt.PART_ID, pt.PART_TYPE]
    if version.major == 1:
        keys += [pt.V1_LOCATION, pt.V1_TABLE]
    m: MetaEntry = {k: table[k] for k in keys}
    return [m]


def get_attr_meta(attr: Part, table_id: PartId, version: Version,
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


def map_ids(mappings: Dict[PartId, PartId], part_ids: List[PartId],
            ver: Version) -> List[PartId]:
    if ver.major == 1:
        return flatten([mappings[id] for id in part_ids])
    else:
        return part_ids


def get_part_ids(parts: List[Part]) -> List[PartId]:
    return list(map(pt.get_partID, parts))


def get_mapped_table_id(data: PartData, table_id: PartId,
                        version: Version) -> PartId:
    if version.major == 1:
        return data.mappings[table_id][0]
    else:
        return table_id


def get_mapped_attr_id(data: PartData, attr_id: PartId,
                       version: Version) -> PartId:
    if version.major == 1:
        return data.mappings[attr_id][0]
    else:
        return attr_id


def table_items(data: PartData, version: Version):
    """Iterates over all tables.

    Yields a tuple of: (original id, mapped id, part).
    """
    for table_id0, td in data.table_data.items():
        table_id1 = get_mapped_table_id(data, table_id0, version)
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
        attr_id1 = get_mapped_attr_id(data, attr_id0, version)
        yield (attr_id0, attr_id1, cs_data)


def attr_items(data: PartData, table_id: PartId, version: Version):
    """Iterates over all attributes in a table.

    Yields a tuple of: (original id, mapped id, part)."""
    for attr in data.table_data[table_id].attributes:
        attr_id0 = pt.get_partID(attr)
        attr_id1 = get_mapped_attr_id(data, attr_id0, version)
        yield (attr_id0, attr_id1, attr)


def attr_items2(data: PartData, table_id: PartId, key: str):
    """Iterates over all attribute parts with `key`, which is part of table
    `table_id`, from `data`."""
    return filter(lambda part: key in part,
                  data.table_data[table_id].attributes)


def init_table_schema2(schema, data, table, version):
    """This is a helper for creating the table schema, to make it easier to
    write rule-functions. This should be prefered over using
    `init_table_schema` directly."""
    # This is not part of module 'schemas' due to simplicity. It has
    # dependencies in this file and the modules may be merged soon enough.
    table_id0 = pt.get_partID(table)
    table_id1 = get_mapped_table_id(data, table_id0, version)
    table_meta = get_table_meta(table, version)
    return init_table_schema(table_id1, table_meta, {})


def set_attr_schema(table_schema, data, table, attr, rule_id, odm_key,
                    cerb_rule, version, typed):
    table_id0 = pt.get_partID(table)
    table_id1 = list(table_schema.keys())[0]
    attr_id0 = pt.get_partID(attr)
    attr_id1 = get_mapped_attr_id(data, attr_id0, version)
    attr_meta = get_attr_meta(attr, table_id0, version, odm_key)
    cerb_type = parse_odm_datatype(attr.get(pt.DATA_TYPE)) if typed else None
    attr_schema = init_attr_schema(attr_id1, rule_id, cerb_rule, cerb_type,
                                   attr_meta)
    deep_update(attr_schema, table_schema[table_id1]['schema']['schema'])


def gen_simple_schema(data: pt.PartData, ver: Version, rule_id: str,
                      odm_key: str, cerb_key: str, value_type_class):
    """Provides a simple way to generate a simple schema. This should be
    prefered to iterating over part-data directly in the rule-functions.

    A simple schema simply means mapping an ODM-attribute to a cerberus schema
    attribute without any extra fuss. Ex: minValue -> min.

    :odm_key: The ODM rule attribute
    :cerb_key: The Cerberus rule name
    :value_type_class: the type-class that should be used to convert the ODM
    value to the Cerberus constraint.
    """
    schema = {}
    typed = cerb_key in {'max', 'min'}
    for table in table_items2(data):
        table_id0 = pt.get_partID(table)
        table_schema = init_table_schema2(schema, data, table, ver)
        for attr in attr_items2(data, table_id0, odm_key):
            cerb_val = value_type_class(attr[odm_key])
            cerb_rule = (cerb_key, cerb_val)
            set_attr_schema(table_schema, data, table, attr, rule_id,
                            odm_key, cerb_rule, ver, typed)
        deep_update(table_schema, schema)
    return schema
