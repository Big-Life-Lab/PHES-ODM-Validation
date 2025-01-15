from copy import deepcopy

import odm_validation.utils as utils
from odm_validation.part_tables import Meta

CerberusSchema = dict
Schema = dict  # {'schemaVersion': str, 'schema': CerberusSchema}

COERCE_KEY = 'coerce'


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


def import_schema(path: str) -> Schema:
    return utils.import_yaml_file(path)


def export_schema(schema: Schema, path: str):
    utils.export_yaml_file(schema, path)
