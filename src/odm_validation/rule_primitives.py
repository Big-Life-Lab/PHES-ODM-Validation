from dataclasses import dataclass
from functools import partial
from logging import error, warning
from typing import Callable, Iterator, Optional
# from pprint import pprint

import odm_validation.odm as odm
import odm_validation.part_tables as pt
import odm_validation.schemas as schemas
from odm_validation.part_tables import (
    Meta, MetaEntry, OdmData, Part, PartId, SomeValue)
from odm_validation.schemas import init_attr_schema, init_table_schema
from odm_validation.stdext import (
    deep_update,
    parse_datetime,
    try_parse_float,
    try_parse_int,
)
from odm_validation.versions import Version


@dataclass(frozen=True)
class OdmValueCtx:
    """ODM value context."""
    value: Optional[str]
    datatype: Optional[str]
    bool_set: set[str]
    null_set: set[str]


AttrPredicate = Callable[[pt.TableId, Part], bool]
GenCerbRulesFunc = Callable[[OdmValueCtx], dict]


def get_table_meta(table: Part, version: Version) -> Meta:
    keys = [pt.PART_ID, pt.PART_TYPE]
    if version.major == 1:
        first = pt.get_initial_version(table)
        if pt.should_have_mapping(table, first, odm.VERSION):
            keys += [pt.V1_LOCATION, pt.V1_TABLE]
    m: MetaEntry = {k: table[k] for k in keys}
    return [m]


def _get_attr_meta(attr: Part, table_id: PartId, version: Version,
                   odm_key: Optional[str] = None,
                   cerb_rules: Optional[dict] = None) -> list:
    result: list = []
    keys = [pt.PART_ID, table_id, pt.table_required_field(table_id)]
    if version.major == 1:
        keys += [pt.V1_LOCATION, pt.V1_TABLE, pt.V1_VARIABLE]
    if odm_key:
        keys += [odm_key]
    result += [{k: attr[k] for k in keys if k in attr}]

    if cerb_rules:
        # pseudo sets
        forbidden_ids = cerb_rules.get('forbidden')
        if forbidden_ids:
            for part_id in forbidden_ids:
                result.append({'partID': part_id, 'partType': pt.MISSINGNESS})

        # sets
        if version.major >= 2:
            allowed_ids = cerb_rules.get('allowed')
            if allowed_ids:
                set_id = attr['mmaSet']

                # XXX: booleanSet's part-ids are lower case in ODM v2.2 and
                # below
                if set_id == pt.BOOLEAN_SET and version.minor <= 2:
                    allowed_ids = list(map(str.lower, allowed_ids))

                for part_id in allowed_ids:
                    result.append({'partID': part_id, 'setID': set_id})
    return result


def get_catset_meta(table_id: PartId, catset: Part, categories: list[Part],
                    version: Version) -> Meta:
    catset_keys = [pt.PART_ID, pt.DATA_TYPE]
    cat_keys = [pt.PART_ID]

    if version.major == 1:
        v1_keys = [pt.V1_LOCATION, pt.V1_TABLE, pt.V1_VARIABLE]
        catset_keys += v1_keys
        cat_keys += v1_keys + [pt.V1_CATEGORY]
    else:
        catset_keys += [table_id]
        if pt.CATSET_ID in catset:
            catset_keys.append(pt.CATSET_ID)

    meta: Meta = []
    meta.append({k: catset[k] for k in catset_keys})
    for cat in categories:
        meta.append({k: cat[k] for k in cat_keys})
        if version.major == 2:
            meta[-1][pt.SET_ID] = catset[pt.CATSET_ID]
    return meta


def get_part_ids(parts: list[Part]) -> list[PartId]:
    return list(map(pt.get_partID, parts))


def _get_mapped_part_ids(data: OdmData, part_id: PartId,
                         version: Version) -> list[PartId]:
    if version.major == 1:
        mapping = data.mappings.get(part_id)
        if mapping:
            return mapping
        else:
            error(f'missing version1 fields in part {part_id}')
    return [part_id]


def _get_mapped_attribute_ids(data: OdmData, attr: Part, version: Version
                              ) -> list[PartId]:
    attr_id = pt.get_partID(attr)
    return _get_mapped_part_ids(data, attr_id, version)


def table_items(data: OdmData, version: Version
                ) -> Iterator[tuple[PartId, PartId, Part]]:
    """Iterates over all tables.

    Yields a tuple of: (original id, mapped id, part).
    """
    for table_id0, td in data.table_data.items():
        for table_id1 in _get_mapped_part_ids(data, table_id0, version):
            table = td.part
            yield (table_id0, table_id1, table)


def attr_items(data: OdmData, table_id0: PartId, table_id1: PartId,
               version: Version, pred: Optional[AttrPredicate] = None
               ) -> Iterator[tuple[str, str, dict]]:
    """Iterates over all attributes in a table.

    Yields a tuple of: (original id, mapped id, part)."""
    attributes = data.table_data[table_id0].attributes

    # filter attributes using `pred`
    if pred:
        pred2 = partial(pred, table_id0)
        attributes = pt.PartMap(
            filter(lambda item: pred2(item[1]), attributes.items()))

    for attr_id0, attr in attributes.items():
        for attr_id1 in _get_mapped_attribute_ids(data, attr, version):
            yield (attr_id0, attr_id1, attr)


def add_attr_schemas(table_schema: dict, data: pt.OdmData, table_id0: str,
                     table_id1: str, attr: Part,
                     rule_id: str, odm_key: Optional[str],
                     cerb_rules: dict, version: Version) -> None:
    for attr_id1 in _get_mapped_attribute_ids(data, attr, version):
        attr_meta = _get_attr_meta(attr, table_id0, version, odm_key,
                                   cerb_rules)
        attr_schema = init_attr_schema(attr_id1, rule_id, cerb_rules,
                                       attr_meta)
        deep_update(table_schema[table_id1]['schema']['schema'], attr_schema)


def init_val_ctx(data: OdmData, attr: Part, odm_key: Optional[str],
                 ) -> Optional[OdmValueCtx]:
    odm_val = attr.get(odm_key)
    if odm_key and odm_val is None:
        # warning(f'missing value for {pt.get_partID(attr)}.{odm_key}')
        return None
    odm_datatype = attr.get(pt.DATA_TYPE)
    return OdmValueCtx(value=odm_val, datatype=odm_datatype,
                       bool_set=data.bool_set, null_set=data.null_set)


def gen_value_schema(data: pt.OdmData, ver: Version, rule_id: str,
                     odm_key: str, gen_cerb_rules: GenCerbRulesFunc) -> dict:
    """Provides a simple way to generate a value schema. This should be
    prefered to iterating over part-data directly in the rule-functions.

    A value-schema is a schema that maps an ODM-attribute to a cerberus schema
    attribute. Ex: minValue -> min.

    :odm_key: The ODM rule attribute
    :gen_cerb_rules: A function returning a dict of Cerberus rules
    """
    schema: dict = {}
    for table_id0, table_id1, table in table_items(data, ver):
        table_meta = get_table_meta(table, ver)
        table_schema = init_table_schema(table_id1, table_meta, {})
        for attr in data.table_data[table_id0].attributes.values():
            val_ctx = init_val_ctx(data, attr, odm_key)
            if not val_ctx:
                continue
            cerb_rules = gen_cerb_rules(val_ctx)
            if not cerb_rules:
                continue
            add_attr_schemas(table_schema, data, table_id0, table_id1, attr,
                             rule_id, odm_key, cerb_rules, ver)
        deep_update(schema, table_schema)
    return schema


def is_mandatory(table_id: pt.TableId, attr: Part) -> bool:
    # Checks whether an attribute is mandatory in a table
    req_key = pt.table_required_field(table_id)
    req_val = attr.get(req_key)
    return req_val == pt.MANDATORY


def is_primary_key(table_id: pt.TableId, attr: Part) -> bool:
    return attr.get(table_id) == pt.ColumnKind.PK.value


def gen_conditional_schema(data: pt.OdmData, ver: Version, rule_id: str,
                           gen_cerb_rules: GenCerbRulesFunc,
                           pred: AttrPredicate) -> dict:
    """Helper function to generate a cerberus schema that implements an ODM
    validation rule. Uses `pred` to decide whether an entry should be created
    for an attribute in a table.
    """
    schema: dict = {}
    odm_key = None
    table_attr: dict = {}
    for table_id0, table_id1, table in table_items(data, ver):
        table_meta = get_table_meta(table, ver)
        table_schema = init_table_schema(table_id1, table_meta, {})

        # There can be multiple mapped table ids for every table,
        # so we should only do this once for every original table id.
        if table_id0 not in table_attr:
            table_attr[table_id0] = list(
                filter(lambda attr: pred(table_id0, attr),
                       data.table_data[table_id0].attributes.values()))

        for attr in table_attr[table_id0]:
            val_ctx = init_val_ctx(data, attr, odm_key)
            if not val_ctx:
                continue
            cerb_rules = gen_cerb_rules(val_ctx)
            add_attr_schemas(table_schema, data, table_id0, table_id1, attr,
                             rule_id, odm_key, cerb_rules, ver)
        deep_update(schema, table_schema)
    return schema


def _odm_to_cerb_datatype(odm_datatype: Optional[str]) -> Optional[str]:
    """converts odm datatype to cerb rule type"""
    t = odm_datatype
    if t in ['boolean', 'categorical', 'varchar']:
        return 'string'
    elif t in ['datetime', 'integer', 'float']:
        return t
    else:
        warning(f'conversion of odm datatype "{t}" is not implemented')
        return None


def gen_cerb_rules_for_type(val_ctx: OdmValueCtx) -> dict:
    odm_type = val_ctx.datatype
    cerb_type = _odm_to_cerb_datatype(odm_type)
    result: dict = {}
    if cerb_type:
        result['type'] = cerb_type
        if cerb_type != 'string':
            result[schemas.COERCE_KEY] = cerb_type
        if odm_type == 'boolean':
            result['allowed'] = sorted(val_ctx.bool_set)
    return result


def parse_odm_val(val_ctx: OdmValueCtx) -> Optional[SomeValue]:
    """Parses the ODM value from `val_ctx`."""
    val = val_ctx.value
    kind = val_ctx.datatype
    if val is None:
        return None
    if kind == 'integer':
        return try_parse_int(val)
    elif kind == 'float':
        return try_parse_float(val)
    elif kind == 'datetime':
        return parse_datetime(val)
    elif kind == 'varchar':
        return str(val)
    else:
        warning(f'parsing of odm datatype "{kind}" is not implemented')
        return None
