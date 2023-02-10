"""This file defines the Rule type along with all the rule implementations.

Rule functions are ordered alphabetically.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Tuple

import part_tables as pt
from schemas import Schema, update_schema
from stdext import (
    try_parse_int,
)
from rule_primitives import (
    OdmValueCtx,
    attr_items,
    gen_cerb_rules_for_type,
    gen_conditional_schema,
    gen_value_schema,
    get_catset_meta,
    get_table_meta,
    is_mandatory,
    is_primary_key,
    parse_odm_val,
    table_items,
)
from versions import Version

COERCION_RULE_ID = '_coercion'


@dataclass(frozen=True)
class Rule:
    """An immutable validation rule.

    `get_error_template` may return a string containing the following
    placeholders (in curly brackets):
    - column_id
    - constraint
    - row_num
    - rule_name
    - table_id
    - value
    - value_len
    - value_type
    """
    id: str
    keys: List[str]
    is_warning: bool
    gen_schema: Callable[pt.PartData, Schema]
    get_error_template: Callable[[Any, str], str]

    match_all_keys: bool
    """Used when mapping a Cerberus error to its ODM validation rule. It
    decides whether all the Cerberus keys that are part of this rule can be
    mapped to an odm validation rule or just the first one. For example, The
    less_than_min_value rule requires three Cerberus rules for its
    implementation: min, type and coerce. However, only the first one should be
    mapped to an min-value error. The missing_values_found rule requires two
    Cerberus rules for its implementation: emptyTrimmed and forbidden. Both of
    these should be mapped to a missing_values_found error."""


def init_rule(rule_id, error, gen_cerb_rules, gen_schema,
              is_warning=False, match_all_keys=False):
    """
    - `error` can either be a string or a function taking a value and returning
      a string.
    - `gen_cerb_rules` must accept a dummy context of `None` values, and return
      a dict with cerberus rule names as keys.
    """
    dummy_ctx = OdmValueCtx(value=1, datatype='integer', bool_set=set(),
                            null_set=set())
    cerb_keys = list(gen_cerb_rules(dummy_ctx).keys())
    get_error_template = error if callable(error) else (lambda x, y: error)
    return Rule(
        id=rule_id,
        keys=cerb_keys,
        is_warning=is_warning,
        match_all_keys=match_all_keys,
        get_error_template=get_error_template,
        gen_schema=gen_schema,
    )


def duplicate_entries_found():
    rule_id = duplicate_entries_found.__name__
    err = ('Duplicate entries found in rows {row_num} with primary key column '
           '{column_id} and primary key value {value} in table {table_id}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {'unique': True}

    def gen_schema(data: pt.PartData, ver):
        return gen_conditional_schema(data, ver, rule_id, gen_cerb_rules,
                                      is_primary_key)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def greater_than_max_length():
    rule_id = greater_than_max_length.__name__
    odm_key = 'maxLength'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} has length {value_len} which is greater than the max '
           'length of {constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {'maxlength': try_parse_int(val_ctx.value)}

    def gen_schema(data: pt.PartData, ver):
        return gen_value_schema(data, ver, rule_id, odm_key, gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def greater_than_max_value():
    rule_id = greater_than_max_value.__name__
    odm_key = 'maxValue'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} is greater than the allowable maximum value of '
           '{constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {
            'max': parse_odm_val(val_ctx)
        } | gen_cerb_rules_for_type(val_ctx)

    def gen_schema(data: pt.PartData, ver):
        return gen_value_schema(data, ver, rule_id, odm_key, gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def missing_mandatory_column():
    rule_id = missing_mandatory_column.__name__
    err = '{rule_name} {column_id} in table {table_id} in row number {row_num}'

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {'required': True}

    def gen_schema(data: pt.PartData, ver):
        return gen_conditional_schema(data, ver, rule_id, gen_cerb_rules,
                                      is_mandatory)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def missing_values_found():
    # TODO: rename to missing_mandatory_value?
    rule_id = missing_values_found.__name__
    err = ('Mandatory column {column_id} in table {table_id} has a missing '
           'value in row {row_num}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {
            'emptyTrimmed': False,
            'forbidden': sorted(val_ctx.null_set),
        }

    def gen_schema(data: pt.PartData, ver):
        return gen_conditional_schema(data, ver, rule_id, gen_cerb_rules,
                                      is_mandatory)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema,
                     is_warning=True, match_all_keys=True)


def less_than_min_length():
    rule_id = less_than_min_length.__name__
    odm_key = 'minLength'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} has length {value_len} which is less than the min '
           'length of {constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {'minlength': try_parse_int(val_ctx.value)}

    def gen_schema(data: pt.PartData, ver):
        return gen_value_schema(data, ver, rule_id, odm_key, gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def less_than_min_value():
    rule_id = less_than_min_value.__name__
    odm_key = 'minValue'
    err = ('Value {value} in row {row_num} in column {column_id} in table '
           '{table_id} is less than the allowable minimum value of '
           '{constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {
            'min': parse_odm_val(val_ctx)
        } | gen_cerb_rules_for_type(val_ctx)

    def gen_schema(data: pt.PartData, ver):
        return gen_value_schema(data, ver, rule_id, odm_key, gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def invalid_category():
    rule_id = invalid_category.__name__
    cerb_rule_key = 'allowed'
    err = ('{rule_name} {value} found in row {row_num} '
           'for column {column_id} in table {table_id}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {cerb_rule_key: None}

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
                cat_ids1 = pt.map_ids(data.mappings, cat_ids0, ver)
                if len(cat_ids1) == 0:
                    continue
                cerb_rule = (cerb_rule_key, sorted(set(cat_ids1)))
                attr_meta = get_catset_meta(table_id0, cs, categories, ver)
                update_schema(schema, table_id1, attr_id1, rule_id,
                              cerb_rule, table_meta, attr_meta)
        return schema

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def invalid_type():
    rule_id = invalid_type.__name__
    odm_key = 'dataType'
    err_default = ('Value {value} in row {row_num} in column {column_id} in '
                   'table {table_id} has type {value_type} but should be of '
                   'type {constraint} or coercable into a {constraint}')
    err_bool = ('Column {column_id} in row {row_num} in table {table_id} is a '
                'boolean but has value {value}. '
                'Allowed values are {allowed_values}.')
    err_date = ('Column {column_id} in row {row_num} in table {table_id} is a '
                'datetime with value {value} that has an unsupported datetime '
                'format. '
                'Allowed values are ISO 8601 standard full dates, full dates '
                'and times, or full dates and times with timezone.')

    def get_error_template(odm_value: Any, odm_type: str):
        if odm_type == pt.BOOLEAN:
            assert isinstance(odm_value, str)
            return err_bool
        elif odm_type == pt.DATETIME:
            return err_date
        else:
            return err_default

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return gen_cerb_rules_for_type(val_ctx)

    def gen_schema(data: pt.PartData, ver):
        return gen_value_schema(data, ver, rule_id, odm_key, gen_cerb_rules)

    return init_rule(rule_id, get_error_template, gen_cerb_rules, gen_schema)


# This is the collection of all validation rules.
# A tuple is used for immutability.
ruleset: Tuple[Rule] = (
    duplicate_entries_found(),
    greater_than_max_length(),
    greater_than_max_value(),
    invalid_category(),
    invalid_type(),
    less_than_min_length(),
    less_than_min_value(),
    missing_mandatory_column(),
    missing_values_found(),
)
