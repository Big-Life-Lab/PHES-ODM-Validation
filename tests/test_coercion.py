import unittest
# from pprint import pprint

import common
from cerberusext import ContextualCoercer, OdmValidator

common.unused_import_dummy = 1

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
        'message': 'Value 123 in row 1 in column amount in table mytable is '
                   'a string and was coerced into a number',
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
        'message': 'Value 567 in row 2 in column quantity in table mytable is '
                   'a string and was coerced into a number',
        'row': {'quantity': '567'},
        'rowNumber': 2,
        'tableName': 'mytable',
        'validationRuleFields': [],
        'warningType': '_coercion'
    }
]


class TestCoercion(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_extract_coercion_schema(self):
        result = ContextualCoercer._extract_coercion_schema(schema)
        self.assertEqual(result, coercion_schema)

    def test_coerce(self):
        warnings = []
        v = ContextualCoercer(warnings=warnings)
        result = v.coerce(data, schema)
        self.assertEqual(result, coerced_data)
        self.assertEqual(warnings, expected_coercion_warnings)

    def test_coerced_type_validation(self):
        coercion_errors = []
        coercion_warnings = []
        v = OdmValidator(coercion_errors=coercion_errors,
                         coercion_warnings=coercion_warnings)
        self.assertTrue(v.validate(data, schema))
        self.assertEqual(coercion_warnings, expected_coercion_warnings)
        # TODO: self.assertEqual(coercion_errors, expected_coercion_errors)


if __name__ == '__main__':
    unittest.main()
