"""This file defines the Rule type along with all the rule implementations."""

from dataclasses import dataclass
from typing import Callable, Tuple

import part_tables as pt
import utils


@dataclass(frozen=True)
class Rule:
    """An immutable validation rule."""
    id: str
    key: str  # The Cerberus error key identifying the Rule
    gen_schema: Callable[pt.PartData, pt.Schema]  # Cerberus schema gen. func.


def missing_mandatory_column():
    rule_id = missing_mandatory_column.__name__
    cerb_rule = ("required", True)

    def gen_schema(data: pt.PartData):
        schema = {}
        for table_id in data.table_data.keys():
            for attr in data.table_data[table_id].attributes:
                odm_rule = (pt.table_required_field(table_id), pt.MANDATORY)
                if attr.get(odm_rule[0], "").capitalize() != odm_rule[1]:
                    continue
                meta = [{odm_rule[0]: odm_rule[1]}]
                attr_schema = pt.init_attr_schema(rule_id, cerb_rule, attr, meta)
                table_schema = pt.init_table_schema(table_id, attr_schema)
                utils.deep_update(table_schema, schema)
        return schema

    return Rule(
        id=rule_id,
        key=cerb_rule[0],
        gen_schema=gen_schema,
    )


def invalid_category():
    rule_id = invalid_category.__name__
    cerb_rule_key = "allowed"

    def gen_schema(data: pt.PartData):
        schema = {}
        for table_id in data.table_data.keys():
            for cs in data.table_data[table_id].catset_attr:
                cs_id = cs["catSetID"]
                values = data.catset_values[cs_id]
                cerb_rule = (cerb_rule_key, values)
                meta = data.catset_meta[cs_id]
                attr_schema = pt.init_attr_schema(rule_id, cerb_rule, cs, meta)
                table_schema = pt.init_table_schema(table_id, attr_schema)
                utils.deep_update(table_schema, schema)
        return schema

    return Rule(
        id=rule_id,
        key=cerb_rule_key,
        gen_schema=gen_schema
    )


# This is the collection of all validation rules.
# A tuple is used for immutability.
ruleset: Tuple[Rule] = (
    invalid_category(),
    missing_mandatory_column(),
)
