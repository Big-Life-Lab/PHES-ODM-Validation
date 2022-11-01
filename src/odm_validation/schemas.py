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
                     meta: Meta):
    return {
        attr_id: {
            cerb_rule[0]: cerb_rule[1],
            'meta': [
                {
                    'ruleID': rule_id,
                    'meta': meta,
                },
                # {
                #     'ruleID': another_rule_using_this_attr,
                #     'meta': [
                #         meta_for_attr_used_with_this_rule,
                #         meta_for_another_attr_used_with_this_rule,
                #     ]
                # }
            ]
        }
    }


def update_schema(schema, table_id, attr_id, rule_id, cerb_rule,
                  table_meta: Meta, attr_meta: Meta):
    attr_schema = init_attr_schema(attr_id, rule_id, cerb_rule, attr_meta)
    table_schema = init_table_schema(table_id, table_meta, attr_schema)
    deep_update(table_schema, schema)
