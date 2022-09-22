import os
import unittest
from copy import deepcopy
from os.path import join

import context

import utils
from part_tables import Schema
from validation import validate_data

context.unused_import_dummy = 1

missing_mandatory_column_pass = {
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

missing_mandatory_column_fail = deepcopy(missing_mandatory_column_pass)
missing_mandatory_column_fail['addresses'][0].pop('addID')

invalid_category_pass = {
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

invalid_category_fail = deepcopy(invalid_category_pass)
invalid_category_fail['samples'][0]['coll'] = 'flow'


class TestValiation(unittest.TestCase):
    def setUp(self):
        dir = os.path.dirname(os.path.realpath(__file__))
        path = join(dir, '../assets/validation-schemas/schema-v2.0.0-rc.1.yml')
        self.schema = utils.import_schema(path)

    def test_schema(self):
        self.assertIsInstance(self.schema, Schema)
        self.assertNotEqual(self.schema, {})

    def test_missing_mandatory_column(self):
        report = validate_data(self.schema, missing_mandatory_column_pass)
        self.assertTrue(report.valid())
        self.assertEqual(len(report.errors), 0)

        report = validate_data(self.schema, missing_mandatory_column_fail)
        self.assertFalse(report.valid())
        self.assertEqual(len(report.errors), 1)
        e = report.errors[0]
        self.assertEqual(e['errorType'], 'missing_mandatory_column')
        self.assertEqual(e['columnName'], 'addID')

    def test_invalid_category(self):
        report = validate_data(self.schema, invalid_category_pass)
        self.assertTrue(report.valid())

        report = validate_data(self.schema, invalid_category_fail)
        self.assertFalse(report.valid())
        self.assertEqual(len(report.errors), 1)
        e = report.errors[0]
        self.assertEqual(e['errorType'], 'invalid_category')
        self.assertEqual(e['columnName'], 'coll')
        self.assertEqual(e['invalidValue'], 'flow')


if __name__ == '__main__':
    unittest.main()
