import unittest
# from pprint import pprint

from odm_validation.cerberusext import ContextualCoercer
from odm_validation.validation import _validate_data_ext

import common


column_meta = [
    {
        'ruleID': 'myrule1',
        'meta': [{'a': 'b'}]
    },
    {
        'ruleID': 'myrule2',
        'meta': [{'c': 'd'}]
    }
]


schema = {
    'schemaVersion': '2.0.0',
    'schema': {
        'mytable': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'amount': {
                        'type': 'float',
                        'coerce': 'float',
                        'meta': column_meta,
                    },
                    'quantity': {
                        'type': 'integer',
                        'coerce': 'integer',
                    },
                    'some_missing_field': {
                    }
                }
            }
        }
    }
}
cerb_schema = schema['schema']

coercion_schema = {
    'mytable': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'amount': {
                    'check_with': 'float',
                    'meta': column_meta,
                },
                'quantity': {
                    'check_with': 'integer',
                }
            }
        }
    }
}

data = {
    'mytable': [
        {'amount': '123', 'unknown': 'asd'},
        {'quantity': '567'},
    ]
}

coerced_data = {
    'mytable': [
        {'amount': 123.0, 'unknown': 'asd'},
        {'quantity': 567},
    ]
}

expected_coercion_warnings = [
    {
        'coercionRules': ['myrule1', 'myrule2'],
        'columnName': 'amount',
        'invalidValue': '123',
        'message': ('_coercion rule triggered '
                    'in table mytable, column amount, row(s) 1: '
                    'Value \"123\" is a string and was coerced into a number'),
        'row': {'amount': '123', 'unknown': 'asd'},
        'rowNumber': 1,
        'tableName': 'mytable',
        'validationRuleFields': [
            {'a': 'b'},
            {'c': 'd'},
        ],
        'warningType': '_coercion'
    },
    {
        'coercionRules': [],
        'columnName': 'quantity',
        'invalidValue': '567',
        'message': ('_coercion rule triggered '
                    'in table mytable, column quantity, row(s) 2: '
                    'Value \"567\" is a string and was coerced into a number'),
        'row': {'quantity': '567'},
        'rowNumber': 2,
        'tableName': 'mytable',
        'validationRuleFields': [],
        'warningType': '_coercion'
    }
]


class TestCoercion(common.OdmTestCase):
    def setUp(self):
        self.maxDiff = None

    def test_extract_coercion_schema(self):
        result = ContextualCoercer._extract_coercion_schema(cerb_schema)
        self.assertEqual(coercion_schema, result)

    def test_coerce(self):
        warnings = []
        v = ContextualCoercer(warnings=warnings)
        result = v.coerce(data, cerb_schema, 0)
        self.assertEqual(coerced_data, result)
        self.assertEqual(expected_coercion_warnings, warnings)

    def test_validation(self):
        report = _validate_data_ext(schema, data)
        self.assertTrue(report.valid())


if __name__ == '__main__':
    unittest.main()
