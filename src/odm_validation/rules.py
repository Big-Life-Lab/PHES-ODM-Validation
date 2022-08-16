"""This file defines the Rule type along with all the rule implementations."""

from dataclasses import dataclass
from typing import Callable, Tuple

import part_tables as pt
import utils


@dataclass(frozen=True)
class Rule:
    """An immutable validation rule."""
    name: str  # Rule name
    key: str  # The Cerberus error key identifying the Rule
    gen_schema: Callable[pt.PartData, pt.Schema]  # Cerberus schema gen. func.


def missing_mandatory_column():
    cerb_rule = ("required", True)

    def gen_schema(data: pt.PartData):
        schema = {}
        for table in data.tables:
            for attr_row in data.table_attr_rows[table]:
                odm_rule = (table + "Required", pt.MANDATORY)
                if attr_row.get(odm_rule[0], "").capitalize() != odm_rule[1]:
                    continue
                meta = [{odm_rule[0]: odm_rule[1]}]
                attr_schema = pt.init_attr_schema(cerb_rule, attr_row, meta)
                table_schema = pt.init_table_schema(table, attr_schema)
                utils.deep_update(table_schema, schema)
        return schema

    return Rule(
        name="Missing mandatory column",
        key=cerb_rule[0],
        gen_schema=gen_schema,
    )


def invalid_category():
    cerb_rule_key = "allowed"

    def gen_schema(data: pt.PartData):
        schema = {}
        for table in data.tables:
            for row in data.table_catset_attr_rows[table]:
                catset = row["catSetID"]
                values = data.catset_values[catset]
                cerb_rule = (cerb_rule_key, values)
                meta = data.catset_meta[catset]
                attr_schema = pt.init_attr_schema(cerb_rule, row, meta)
                table_schema = pt.init_table_schema(table, attr_schema)
                utils.deep_update(table_schema, schema)
        return schema

    return Rule(
        name="Invalid category",
        key=cerb_rule_key,
        gen_schema=gen_schema
    )


# This is an immutable collection of all the validation rules.
ruleset: Tuple[Rule] = (
    invalid_category(),
    missing_mandatory_column(),
)
