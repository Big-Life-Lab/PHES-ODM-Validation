"""This file defines the Rule type along with all the rule implementations.

Rule functions are ordered alphabetically.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import part_tables as pt
from schemas import Schema, update_schema
from versions import Version

from rule_primitives import attr_items, \
                            gen_simple_schema, \
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
    - value_len
    - constraint
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


def greater_than_max_length():
    rule_id = greater_than_max_length.__name__
    odm_key = 'maxLength'
    cerb_key = 'maxlength'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} has length {value_len} which is greater than the max '
           'length of {constraint}')

    def gen_schema(data: pt.PartData, ver):
        return gen_simple_schema(data, ver, rule_id, odm_key, cerb_key, int)

    return init_rule(rule_id, cerb_key, err, gen_schema)


def greater_than_max_value():
    rule_id = greater_than_max_value.__name__
    odm_key = 'maxValue'
    cerb_key = 'max'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} is greater than the allowable maximum value of '
           '{constraint}')

    def gen_schema(data: pt.PartData, ver):
        return gen_simple_schema(data, ver, rule_id, odm_key, cerb_key, float)

    return init_rule(rule_id, cerb_key, err, gen_schema)


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


def less_than_min_length():
    rule_id = less_than_min_length.__name__
    odm_key = 'minLength'
    cerb_key = 'minlength'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} has length {value_len} which is less than the min '
           'length of {constraint}')

    def gen_schema(data: pt.PartData, ver):
        return gen_simple_schema(data, ver, rule_id, odm_key, cerb_key, int)

    return init_rule(rule_id, cerb_key, err, gen_schema)


def less_than_min_value():
    rule_id = less_than_min_value.__name__
    odm_key = 'minValue'
    cerb_key = 'min'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} is less than the allowable minimum value of '
           '{constraint}')

    def gen_schema(data: pt.PartData, ver):
        return gen_simple_schema(data, ver, rule_id, odm_key, cerb_key, float)

    return init_rule(rule_id, cerb_key, err, gen_schema)


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
    greater_than_max_length(),
    greater_than_max_value(),
    invalid_category(),
    less_than_min_length(),
    less_than_min_value(),
    missing_mandatory_column(),
)
