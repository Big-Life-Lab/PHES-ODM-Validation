import unittest
from copy import deepcopy
from os.path import join

import common
import utils
from validation import generate_validation_schema, validate_data

asset_dir = join(common.root_dir,
                 'assets/validation-rules/invalid-category')

parts_v2 = utils.import_dataset(join(asset_dir, 'parts.csv'))
schema_v1 = utils.import_schema(join(asset_dir, 'schema-v1.yml'))
schema_v2 = utils.import_schema(join(asset_dir, 'schema-v2.yml'))


invalid_category_pass_v1 = {
    'Sample': [
        {
            'Collection': 'FlowPr',
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


class TestInvalidCategory(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_schema_generation_v1(self):
        result = generate_validation_schema(parts_v2, schema_version='1.0.0')
        self.assertDictEqual(schema_v1, result)

    def test_schema_generation_v2(self):
        result = generate_validation_schema(parts_v2, schema_version='2.0.0')
        got = result['schema']['samples']
        expected = schema_v2['schema']['samples']
        self.assertDictEqual(expected, got)

    def invalid_category_impl(self, schema, invalid_value_column,
                              invalid_value, data_pass, data_fail):
        report = validate_data(schema, data_pass)
        self.assertTrue(report.valid())
        report = validate_data(schema, data_fail)
        self.assertFalse(report.valid(), report.errors)
        self.assertEqual(len(report.errors), 1)
        e = report.errors[0]
        self.assertEqual(e['errorType'], 'invalid_category')
        self.assertEqual(e['columnName'], invalid_value_column)
        self.assertEqual(e['invalidValue'], invalid_value)

    def test_invalid_category_v1(self):
        self.invalid_category_impl(schema_v1, 'Collection', 'flow',
                                   invalid_category_pass_v1,
                                   invalid_category_fail_v1)

    def test_invalid_category_v2(self):
        self.invalid_category_impl(schema_v2, 'coll', 'flow',
                                   invalid_category_pass_v2,
                                   invalid_category_fail_v2)


if __name__ == '__main__':
    unittest.main()
