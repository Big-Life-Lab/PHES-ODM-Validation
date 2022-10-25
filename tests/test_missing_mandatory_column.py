import unittest
from copy import deepcopy

import common

from validation import generate_validation_schema, validate_data

parts_v2 = [
    {
        'partID': 'addresses',
        'partType': 'table',
        'version1Location': 'tables',
        'version1Table': 'Address',
    },
    {
        'partID': 'contacts',
        'partType': 'table',
        'version1Location': 'tables',
        'version1Table': 'Contact',
    },
    {
        'partID': 'addID',
        'partType': 'attribute',
        'addresses': 'pK',
        'addressesRequired': 'mandatory',
        'version1Location': 'variables',
        'version1Table': 'Address',
        'version1Variable': 'AddressID'
    },
    {
        'partID': 'addL2',
        'partType': 'attribute',
        'addresses': 'header',
        'addressesRequired': 'optional',
        'version1Location': 'variables',
        'version1Table': 'Address',
        'version1Variable': 'AddressLineTwo'
    },
    {
        'partID': 'contID',
        'partType': 'attribute',
        'contacts': 'pK',
        'contactsRequired': 'mandatory',
        'version1Location': 'variables',
        'version1Table': 'Contact',
        'version1Variable': 'ContactID'
    },
]

schema_v1 = {
    'schemaVersion': '1.0.0',
    'schema': {
        'Address': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'AddressID': {
                        'required': True,
                        'meta': [
                            {
                                'ruleID': 'missing_mandatory_column',
                                'meta': [
                                    {
                                        'partID': 'addID',
                                        'addresses': 'pK',
                                        'addressesRequired': 'mandatory',
                                        'version1Location': 'variables',
                                        'version1Table': 'Address',
                                        'version1Variable': 'AddressID'
                                    }
                                ]
                            }
                        ]
                    },
                },
                'meta': [
                    {
                        'partID': 'addresses',
                        # 'partType': 'table',
                        'version1Location': 'tables',
                        'version1Table': 'Address'
                    }
                ]
            }
        },
        'Contact': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'ContactID': {
                        'required': True,
                        'meta': [
                            {
                                'ruleID': 'missing_mandatory_column',
                                'meta': [
                                    {
                                        'partID': 'contID',
                                        'contacts': 'pK',
                                        'contactsRequired': 'mandatory',
                                        'version1Location': 'variables',
                                        'version1Table': 'Contact',
                                        'version1Variable': 'ContactID'
                                    }
                                ]
                            }
                        ]
                    }
                },
                'meta': [
                    {
                        'partID': 'contacts',
                        # 'partType': 'table',
                        'version1Location': 'tables',
                        'version1Table': 'Contact'
                    }
                ]
            },
        },
    }
}

schema_v2 = common.import_schema_v2()

missing_mandatory_column_pass_v1 = {
    'Address': [
        {
            'AddressID': '1',
            'AddL2': 'my street',
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
missing_mandatory_column_fail_v1['Address'][0].pop('AddressID')

missing_mandatory_column_fail_v2 = deepcopy(missing_mandatory_column_pass_v2)
missing_mandatory_column_fail_v2['addresses'][0].pop('addID')


class TestValidateData(unittest.TestCase):
    def test_schema_generation_v1(self):
        result = generate_validation_schema(parts_v2, schema_version='1.0.0')
        self.assertDictEqual(schema_v1, result)

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
        self.missing_mandatory_column_impl(schema_v1, 'AddressID',
                                           missing_mandatory_column_pass_v1,
                                           missing_mandatory_column_fail_v1)

    def test_missing_mandatory_column_v2(self):
        self.missing_mandatory_column_impl(schema_v2, 'addID',
                                           missing_mandatory_column_pass_v2,
                                           missing_mandatory_column_fail_v2)


if __name__ == '__main__':
    unittest.main()
