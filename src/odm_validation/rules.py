"""This file defines the Rule type along with all the rule implementations."""

from dataclasses import dataclass
from typing import Callable, Tuple

import part_tables as pt


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
    gen_schema: Callable[pt.PartData, pt.Schema]  # Cerberus schema gen. func.


def missing_mandatory_column():
    rule_id = missing_mandatory_column.__name__
    cerb_rule = ('required', True)
    err = '{rule_name} {column_id} in table {table_id} in row number {row_num}'

    def gen_schema(data: pt.PartData):
        schema = {}
        for table_id in data.table_data.keys():
            for attr in data.table_data[table_id].attributes:
                odm_rule = (pt.table_required_field(table_id), pt.MANDATORY)
                if attr.get(odm_rule[0], '').capitalize() != odm_rule[1]:
                    continue
                attr_id = pt.get_partID(attr)
                meta = [{odm_rule[0]: odm_rule[1]}]
                pt.update_schema(schema, table_id, attr_id, rule_id, cerb_rule,
                                 meta)
        return schema

    return Rule(
        id=rule_id,
        key=cerb_rule[0],
        error_template=err,
        gen_schema=gen_schema,
    )


def invalid_category():
    rule_id = invalid_category.__name__
    cerb_rule_key = 'allowed'
    err = ('{rule_name} {value} found in row {row_num} '
           'for column {column_id} in table {table_id}')

    def gen_schema(data: pt.PartData):
        schema = {}
        for table_id in data.table_data.keys():
            for attr_id, cs_data in data.catset_data.items():
                if table_id not in cs_data.tables:
                    continue
                cerb_rule = (cerb_rule_key, cs_data.values)
                pt.update_schema(schema, table_id, attr_id, rule_id, cerb_rule,
                                 cs_data.meta)
        return schema

    return Rule(
        id=rule_id,
        key=cerb_rule_key,
        error_template=err,
        gen_schema=gen_schema
    )


# This is the collection of all validation rules.
# A tuple is used for immutability.
ruleset: Tuple[Rule] = (
    invalid_category(),
    missing_mandatory_column(),
)
