from typing import Dict, List

import part_tables as pt
from part_tables import Meta, MetaEntry, Part, PartData, PartId
from stdext import flatten
from versions import Version


def get_table_meta(table: Part, version: Version) -> Meta:
    keys = [pt.PART_ID, pt.PART_TYPE]
    if version.major == 1:
        keys += [pt.V1_LOCATION, pt.V1_TABLE]
    m: MetaEntry = {k: table[k] for k in keys}
    return [m]


def get_attr_meta(attr: Part, table_id: PartId, version: Version):
    keys = [pt.PART_ID, table_id, pt.table_required_field(table_id)]
    if version.major == 1:
        keys += [pt.V1_LOCATION, pt.V1_TABLE, pt.V1_VARIABLE]
    return [{k: attr[k] for k in keys}]


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
