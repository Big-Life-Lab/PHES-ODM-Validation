from logging import warning
from typing import Optional

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


def init_attr_schema(attr_id: str, rule_id: str, cerb_rule: tuple,
                     cerb_type: Optional[str], meta: Meta):
    # ['meta'] is a list with one entry per rule.
    # ['meta']['meta'] is a `Meta` with one `MetaEntry` per part.
    inner = {
        cerb_rule[0]: cerb_rule[1],
        'meta': [
            {
                'ruleID': rule_id,
                'meta': meta,
            }
        ]
    }
    if cerb_type:
        inner['type'] = cerb_type
        if cerb_type != 'string':
            inner['coerce'] = cerb_type
    return {attr_id: inner}


def parse_odm_datatype(odm_datatype) -> Optional[str]:
    """returns the cerberus-equivalent type"""
    t = odm_datatype
    if not t:
        return
    if t in ['categorical', 'varchar']:
        return 'string'
    if t in ['integer', 'float']:
        return t
    warning(f'odm datatype {odm_datatype} is not implemented')


def update_schema(schema, table_id, attr_id, rule_id, cerb_rule,
                  table_meta: Meta, attr_meta: Meta):
    attr_schema = init_attr_schema(attr_id, rule_id, cerb_rule, None,
                                   attr_meta)
    table_schema = init_table_schema(table_id, table_meta, attr_schema)
    deep_update(table_schema, schema)
