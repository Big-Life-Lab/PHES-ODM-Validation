import unittest
from copy import deepcopy

import common

from validation import validate_data

schema_v2 = common.import_schema_v2()

schema_v1 = {
    'schemaVersion': '1',
    'schema': {
        'Address': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'addressID': {
                        'required': True,
                    },
                    'addL2': {}
                },
            }
        },
        'Contact': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'contactID': {
                        'required': True,
                    }
                }
            },
        },
    }
}

missing_mandatory_column_pass_v1 = {
    'Address': [
        {
            'addressID': '1',
            'addL2': 'my street',
        }
    ]
}

missing_mandatory_column_pass_v2 = {
    'addresses': [
        {
            'addID': '1',
            'addL1': 'my street',
            'city': 'my city',
            'country': 'my country',
            'dataID': '1',
            'stateProvReg': 'x',
        }
    ]
}

missing_mandatory_column_fail_v1 = deepcopy(missing_mandatory_column_pass_v1)
missing_mandatory_column_fail_v1['Address'][0].pop('addressID')

missing_mandatory_column_fail_v2 = deepcopy(missing_mandatory_column_pass_v2)
missing_mandatory_column_fail_v2['addresses'][0].pop('addID')


class TestValidateData(unittest.TestCase):
    def missing_mandatory_column_impl(self, schema, column,
                                      data_pass, data_fail):
        report = validate_data(schema, data_pass)
        self.assertTrue(report.valid(), report.errors)
        self.assertEqual(len(report.errors), 0)
        report = validate_data(schema, data_fail)
        self.assertFalse(report.valid(), report.errors)
        self.assertEqual(len(report.errors), 1)
        e = report.errors[0]
        self.assertEqual(e['errorType'], 'missing_mandatory_column')
        self.assertEqual(e['columnName'], column)

    def test_missing_mandatory_column_v1(self):
        self.missing_mandatory_column_impl(schema_v1, 'addressID',
                                           missing_mandatory_column_pass_v1,
                                           missing_mandatory_column_fail_v1)

    def test_missing_mandatory_column_v2(self):
        self.missing_mandatory_column_impl(schema_v2, 'addID',
                                           missing_mandatory_column_pass_v2,
                                           missing_mandatory_column_fail_v2)


if __name__ == '__main__':
    unittest.main()
