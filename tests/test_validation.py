import logging
import os
import sys
import unittest
from copy import deepcopy
from os.path import join

import context

import utils
from part_tables import Schema
from validation import validate_data

context.unused_import_dummy = 1

dir = os.path.dirname(os.path.realpath(__file__))
path = join(dir, '../assets/validation-schemas/schema-v2.0.0-rc.1.yml')
schema_v2 = utils.import_schema(path)

schema_v1 = {
    "schemaVersion": "1",
    "schema": {
        "Address": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "AddressId": {
                        "required": True,
                        "meta": [
                            {
                                "ruleId": "missing_mandatory_column",
                                "meta": [
                                    {
                                        "partID": "addressID",
                                        "addressesRequired": "mandatory",
                                        "version1Location": "variables",
                                        "verion1Table": "Address",
                                        "version1Variable": "AddressId"
                                    }
                                ]
                            }
                        ]
                    },
                    "addL2": {}
                },
                "meta": {
                    "partID": "addresses",
                    "partType": "table",
                    "version1Location": "tables",
                    "verion1Table": "Address"
                }
            }
        },
        "Contact": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "ContactId": {
                        "required": True,
                        "meta": [
                            {
                                "ruleId": "missing_mandatory_column",
                                "meta": [
                                    {
                                        "partID": "contactID",
                                        "contactsRequired": "mandatory",
                                        "version1Location": "variables",
                                        "verion1Table": "Contact",
                                        "version1Variable": "ContactId"
                                    }
                                ]
                            }
                        ]
                    }
                }
            },
            "meta": {
                "partID": "contacts",
                "partType": "table",
                "version1Location": "tables",
                "verion1Table": "Contact"
            }
        },
        "Sample": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "Collection": {
                        "type": "string",
                        "allowed": ["Comp3h", "Comp8h", "FlowPR", "flowRatePr"],
                        "meta": [
                            {
                                "ruleId": "invalid_category",
                                "meta": [
                                    {
                                        "partID": "collection",
                                        "samples": "header",
                                        "dataType": "categorical",
                                        "catSetID": "collectCat",
                                        "version1Location": "variables",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection"
                                    },
                                    {
                                        "partID": "comp3h",
                                        "partType": "category",
                                        "catSetID": "collectCat",
                                        "version1Location": "variableCategories",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection",
                                        "version1Category": "Comp3h"
                                    },
                                    {
                                        "partID": "comp8h",
                                        "partType": "category",
                                        "catSetID": "collectCat",
                                        "version1Location": "variableCategories",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection",
                                        "version1Category": "Comp8h"
                                    },
                                    {
                                        "partID": "flowPr",
                                        "partType": "category",
                                        "catSetID": "collectCat",
                                        "version1Location": "variableCategories",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection",
                                        "version1Category": "FlowPR; flowRatePr"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
    }
}

missing_mandatory_column_pass_v1 = {
    'Address': [
        {
            'AddressId': '1',
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
missing_mandatory_column_fail_v1['Address'][0].pop('AddressId')

missing_mandatory_column_fail_v2 = deepcopy(missing_mandatory_column_pass_v2)
missing_mandatory_column_fail_v2['addresses'][0].pop('addID')

invalid_category_pass_v1 = {
    'Sample': [
        {
            'Collection': 'FlowPR',
        }
    ]
}

invalid_category_pass_v2 = {
    'samples': [
        {
            'coll': 'flowPr',
            'cDT': 'x',
            'saMaterial': 'afu',
            'sampID': '1',
            'siteID': '1',
            'parSampID': '1',
            'dataID': '1',
            'contID': '1',
            'collPer': 'x',
            'collNum': 'x',
        }
    ]
}

invalid_category_fail_v1 = deepcopy(invalid_category_pass_v1)
invalid_category_fail_v1['Sample'][0]['Collection'] = 'flow'

invalid_category_fail_v2 = deepcopy(invalid_category_pass_v2)
invalid_category_fail_v2['samples'][0]['coll'] = 'flow'


class TestValiation(unittest.TestCase):
    def setUp(self):
        # # the info log from validate_data shows current schema version
        # logging.getLogger().level = logging.INFO
        self.schemas = {'v1': schema_v1, 'v2': schema_v2}

    def test_schema(self):
        for _, schema in self.schemas.items():
            self.assertIsInstance(schema, Schema)
            self.assertNotEqual(schema, {})

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
        self.missing_mandatory_column_impl(self.schemas['v1'], 'AddressId',
                                           missing_mandatory_column_pass_v1,
                                           missing_mandatory_column_fail_v1)

    def test_missing_mandatory_column_v2(self):
        self.missing_mandatory_column_impl(self.schemas['v2'], 'addID',
                                           missing_mandatory_column_pass_v2,
                                           missing_mandatory_column_fail_v2)

    def invalid_category_impl(self, schema, column, value,
                              data_pass, data_fail):
        report = validate_data(schema, data_pass)
        self.assertTrue(report.valid())

        report = validate_data(schema, data_fail)
        self.assertFalse(report.valid())
        self.assertEqual(len(report.errors), 1)
        e = report.errors[0]
        self.assertEqual(e['errorType'], 'invalid_category')
        self.assertEqual(e['columnName'], column)
        self.assertEqual(e['invalidValue'], value)

    def test_invalid_category_v1(self):
        self.invalid_category_impl(self.schemas['v1'], 'Collection', 'flow',
                                   invalid_category_pass_v1,
                                   invalid_category_fail_v1)

    def test_invalid_category_v2(self):
        self.invalid_category_impl(self.schemas['v2'], 'coll', 'flow',
                                   invalid_category_pass_v2,
                                   invalid_category_fail_v2)


if __name__ == '__main__':
    unittest.main()
