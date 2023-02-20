from copy import deepcopy

from part_tables import Meta
from stdext import deep_update

CerberusSchema = dict
Schema = dict  # {'schemaVersion': str, 'schema': CerberusSchema}


def init_table_schema(table_id, table_meta, attr_schema):
    return {
        table_id: {
            'type': 'list',  # each table has a list of rows
            'schema': {
                'type': 'dict',  # each row is a dict
                'schema': attr_schema,
                'meta': table_meta,
            },
        }
    }


def init_attr_schema(attr_id: str, rule_id: str, cerb_rules: dict,
                     meta: Meta):
    # - uses deepcopy to avoid mutating `cerb_rules`
    # - ['meta'] is a list with one entry per rule.
    # - ['meta']['meta'] is a `Meta` with one `MetaEntry` per part.
    inner = deepcopy(cerb_rules)
    inner['meta'] = [
        {
            'ruleID': rule_id,
            'meta': meta,
        }
    ]
    return {attr_id: inner}


def update_schema(schema, table_id, attr_id, rule_id, cerb_rule,
                  table_meta: Meta, attr_meta: Meta):
    cerb_rules = {cerb_rule[0]: cerb_rule[1]}
    attr_schema = init_attr_schema(attr_id, rule_id, cerb_rules, attr_meta)
    table_schema = init_table_schema(table_id, table_meta, attr_schema)
    deep_update(schema, table_schema)
