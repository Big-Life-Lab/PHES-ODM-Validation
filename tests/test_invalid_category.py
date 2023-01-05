import unittest
from os.path import join

import common
import utils
from validation import generate_validation_schema, validate_data

asset_dir = join(common.root_dir,
                 'assets/validation-rules/invalid-category')

parts_v2 = utils.import_dataset(join(asset_dir, 'parts.csv'))
schema_v1 = utils.import_schema(join(asset_dir, 'schema-v1.yml'))
schema_v2 = utils.import_schema(join(asset_dir, 'schema-v2.yml'))


invalid_category_pass_v2 = {
    'samples': utils.import_dataset(join(asset_dir, 'valid-dataset.csv')),
}

invalid_category_fail_v2 = {
    'samples': utils.import_dataset(join(asset_dir, 'invalid-dataset.csv')),
}


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

    def test_invalid_category_v2(self):
        report = validate_data(schema_v2, invalid_category_pass_v2)
        self.assertTrue(report.valid())
        report = validate_data(schema_v2, invalid_category_fail_v2)
        expected = utils.import_json_file(join(asset_dir, 'error-report.json'))
        self.assertEqual(report.errors, expected['errors'])


if __name__ == '__main__':
    unittest.main()
