"""This file defines the Rule type along with all the rule implementations."""

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import part_tables as pt
from schemas import Schema, update_schema
from versions import Version

from rule_primitives import attr_items, \
                            get_attr_meta, \
                            get_catset_meta, \
                            get_table_meta, \
                            map_ids, \
                            table_items


@dataclass(frozen=True)
class Rule:
    """An immutable validation rule.

    `error_template` may use the following placeholders (in curly brackets):
    - column_id
    - row_num
    - rule_name
    - table_id
    - value
    """
    id: str
    key: str  # The Cerberus error key identifying the Rule
    error_template: str  # The template used to build the error message
    gen_schema: Dict[str, Callable[pt.PartData, Schema]]


def init_rule(rule_id, cerb_key, error, gen_schema):
    return Rule(
        id=rule_id,
        key=cerb_key,
        error_template=error,
        gen_schema=gen_schema,
    )


def missing_mandatory_column():
    rule_id = missing_mandatory_column.__name__
    cerb_rule = ('required', True)
    err = '{rule_name} {column_id} in table {table_id} in row number {row_num}'

    def gen_schema(data: pt.PartData, ver):
        schema = {}
        for table_id0, table_id1, table in table_items(data, ver):
            table_meta = get_table_meta(table, ver)
            for attr_id0, attr_id1, attr in attr_items(data, table_id0, ver):
                req_key = pt.table_required_field(table_id0)
                req_val = attr.get(req_key)
                if req_val != pt.MANDATORY:
                    continue
                attr_meta = get_attr_meta(attr, table_id0, ver)
                update_schema(schema, table_id1, attr_id1, rule_id,
                              cerb_rule, table_meta, attr_meta)
        return schema

    return init_rule(rule_id, cerb_rule[0], err, gen_schema)


def invalid_category():
    rule_id = invalid_category.__name__
    cerb_rule_key = 'allowed'
    err = ('{rule_name} {value} found in row {row_num} '
           'for column {column_id} in table {table_id}')

    def gen_schema(data: pt.PartData, ver: Version):
        schema = {}
        for table_id0, table_id1, table in table_items(data, ver):
            table_meta = get_table_meta(table, ver)
            for attr_id0, attr_id1, attr in attr_items(data, table_id0, ver):
                if not pt.has_catset(attr):
                    continue
                cs_data = data.catset_data[attr_id0]
                cs = cs_data.part
                categories = cs_data.cat_parts
                cat_ids0 = list(map(pt.get_partID, categories))
                cat_ids1 = map_ids(data.mappings, cat_ids0, ver)
                cerb_rule = (cerb_rule_key, cat_ids1)
                attr_meta = get_catset_meta(table_id0, cs, categories, ver)
                update_schema(schema, table_id1, attr_id1, rule_id,
                              cerb_rule, table_meta, attr_meta)
        return schema

    return init_rule(rule_id, cerb_rule_key, err, gen_schema)


# This is the collection of all validation rules.
# A tuple is used for immutability.
ruleset: Tuple[Rule] = (
    invalid_category(),
    missing_mandatory_column(),
)
