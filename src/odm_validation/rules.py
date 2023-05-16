"""This file defines the Rule type along with all the rule implementations.

Rule functions are ordered alphabetically.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Tuple
# from pprint import pprint

import part_tables as pt
from input_data import DataKind
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


RuleId = Enum('RuleId', [
    '_all',
    '_coercion',
    'duplicate_entries_found',
    'greater_than_max_length',
    'greater_than_max_value',
    'missing_mandatory_column',
    'missing_values_found',
    'less_than_min_length',
    'less_than_min_value',
    'invalid_category',
    'invalid_type',
])


@dataclass(frozen=True)
class Rule:
    """An immutable validation rule.

    `get_error_template` may return a string containing the following
    placeholders (in curly brackets):
    - column_id
    - constraint
    - row_num
    - rule_id
    - table_id
    - value
    - value_len
    - value_type
    """
    id: RuleId
    keys: List[str]
    is_column: bool
    is_warning: bool
    gen_schema: Callable[pt.OdmData, Schema]
    get_error_template: Callable[[Any, str, DataKind], str]

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
              is_column=False, is_warning=False, match_all_keys=False):
    """
    - `error` can either be a string or a function taking a value and returning
      a string.
    - `gen_cerb_rules` must accept a dummy context of `None` values, and return
      a dict with cerberus rule names as keys.
    - `is_column` determines if the rule is validating columns/headers.
    """
    dummy_ctx = OdmValueCtx(value=1, datatype='integer', bool_set=set(),
                            null_set=set())
    cerb_keys = list(gen_cerb_rules(dummy_ctx).keys())
    get_error_template = error if callable(error) else (lambda x, y, z: error)
    return Rule(
        id=rule_id,
        keys=cerb_keys,
        is_column=is_column,
        is_warning=is_warning,
        match_all_keys=match_all_keys,
        get_error_template=get_error_template,
        gen_schema=gen_schema,
    )


def duplicate_entries_found():
    rule_id = RuleId.duplicate_entries_found
    err = ('Duplicate entries found with primary key value {value}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {'unique': True}

    def gen_schema(data: pt.OdmData, ver):
        return gen_conditional_schema(data, ver, rule_id.name, gen_cerb_rules,
                                      is_primary_key)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def greater_than_max_length():
    rule_id = RuleId.greater_than_max_length
    odm_key = 'maxLength'
    err = ('Value {value} has length {value_len} which is greater than the '
           'max length of {constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        val = try_parse_int(val_ctx.value)
        if val:
            return {'maxlength': val}

    def gen_schema(data: pt.OdmData, ver):
        return gen_value_schema(data, ver, rule_id.name, odm_key,
                                gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def greater_than_max_value():
    rule_id = RuleId.greater_than_max_value
    odm_key = 'maxValue'
    err = ('Value {value} is greater than the allowable maximum value of '
           '{constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        val = parse_odm_val(val_ctx)
        if val is not None:
            return {'max': val} | gen_cerb_rules_for_type(val_ctx)

    def gen_schema(data: pt.OdmData, ver):
        return gen_value_schema(data, ver, rule_id.name, odm_key,
                                gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def missing_mandatory_column():
    rule_id = RuleId.missing_mandatory_column
    err = 'Missing mandatory column {column_id}'

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {'required': True}

    def gen_schema(data: pt.OdmData, ver):
        return gen_conditional_schema(data, ver, rule_id.name, gen_cerb_rules,
                                      is_mandatory)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema,
                     is_column=True)


def missing_values_found():
    # TODO: rename to missing_mandatory_value?
    rule_id = RuleId.missing_values_found

    def get_error_template(odm_value: Any, odm_type: str, data_kind: DataKind):
        if odm_value == '':
            return 'Empty string found'
        else:
            return 'Missing value {value}'

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {
            'emptyTrimmed': False,
            'forbidden': sorted(val_ctx.null_set),
        }

    def gen_schema(data: pt.OdmData, ver):
        return gen_conditional_schema(data, ver, rule_id.name, gen_cerb_rules,
                                      is_mandatory)

    return init_rule(rule_id, get_error_template, gen_cerb_rules, gen_schema,
                     is_warning=True, match_all_keys=True)


def less_than_min_length():
    rule_id = RuleId.less_than_min_length
    odm_key = 'minLength'
    err = ('Value {value} has length {value_len} which is less than the min '
           'length of {constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        val = try_parse_int(val_ctx.value)
        if val > 0:
            return {'minlength': val}

    def gen_schema(data: pt.OdmData, ver):
        return gen_value_schema(data, ver, rule_id.name, odm_key,
                                gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def less_than_min_value():
    rule_id = RuleId.less_than_min_value
    odm_key = 'minValue'
    err = ('Value {value} is less than the allowable minimum value of '
           '{constraint}')

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        val = parse_odm_val(val_ctx)
        if val is not None:
            return {'min': val} | gen_cerb_rules_for_type(val_ctx)

    def gen_schema(data: pt.OdmData, ver):
        return gen_value_schema(data, ver, rule_id.name, odm_key,
                                gen_cerb_rules)

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def invalid_category():
    rule_id = RuleId.invalid_category
    cerb_rule_key = 'allowed'
    err = 'Invalid category {value}'

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return {cerb_rule_key: None}

    def gen_schema(data: pt.OdmData, ver: Version):
        # FIXME: `cat_ids1` contains duplicates due to v1 categories belonging
        # to multiple tables.
        schema = {}
        other_cat = ['other'] if ver.major == 1 else []
        for table_id0, table_id1, table in table_items(data, ver):
            table_meta = get_table_meta(table, ver)
            for attr_id0, attr_id1, attr in attr_items(data, table_id0,
                                                       table_id1, ver):
                cs_data = data.catset_data.get((table_id0, attr_id0))
                if not cs_data:
                    continue
                cs = cs_data.part
                categories = cs_data.cat_parts
                cat_ids0 = list(map(pt.get_partID, categories))
                cat_ids1 = pt.map_ids(data.mappings, cat_ids0, ver)
                if len(cat_ids1) == 0:
                    continue
                cerb_rule = (cerb_rule_key, sorted(set(cat_ids1 + other_cat)))
                attr_meta = get_catset_meta(table_id0, cs, categories, ver)
                update_schema(schema, table_id1, attr_id1, rule_id.name,
                              cerb_rule, table_meta, attr_meta)
        return schema

    return init_rule(rule_id, err, gen_cerb_rules, gen_schema)


def invalid_type():
    rule_id = RuleId.invalid_type
    odm_key = 'dataType'
    err_default = ('Value {value} has type {value_type} but should be of '
                   'type {constraint} or coercable into a {constraint}')
    err_bool = ('Column {column_id} is a boolean but has value {value}. '
                'Allowed values are {allowed_values}.')
    err_date = ('Column {column_id} is a datetime but has value {value}. '
                'Allowed values are ISO 8601 standard full dates, full dates '
                'and times, or full dates and times with timezone.')

    def get_error_template(odm_value: Any, odm_type: str, data_kind: DataKind):
        if odm_type == pt.BOOLEAN:
            assert isinstance(odm_value, str)
            return err_bool
        elif odm_type == pt.DATETIME:
            return err_date
        else:
            return err_default

    def gen_cerb_rules(val_ctx: OdmValueCtx):
        return gen_cerb_rules_for_type(val_ctx)

    def gen_schema(data: pt.OdmData, ver):
        return gen_value_schema(data, ver, rule_id.name, odm_key,
                                gen_cerb_rules)

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
