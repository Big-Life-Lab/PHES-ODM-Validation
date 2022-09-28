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
                    "addressID": {
                        "required": True,
                    },
                    "addL2": {}
                },
            }
        },
        "Contact": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "contactID": {
                        "required": True,
                    }
                }
            },
        },
        "Sample": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "collection": {
                        "type": "string",
                        "allowed": ["comp3h", "comp8h", "flowPR", "flowRatePr"],
                    }
                }
            }
        }
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

invalid_category_pass_v1 = {
    'Sample': [
        {
            'collection': 'flowPR',
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
invalid_category_fail_v1['Sample'][0]['collection'] = 'flow'

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
        self.missing_mandatory_column_impl(self.schemas['v1'], 'addressID',
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

    def test_invalid_catecory_v1(self):
        self.invalid_category_impl(self.schemas['v1'], 'collection', 'flow',
                                   invalid_category_pass_v1,
                                   invalid_category_fail_v1)

    def test_invalid_category_v2(self):
        self.invalid_category_impl(self.schemas['v2'], 'coll', 'flow',
                                   invalid_category_pass_v2,
                                   invalid_category_fail_v2)


if __name__ == '__main__':
    unittest.main()
