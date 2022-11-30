import unittest
from os.path import join

import common
import utils
from validation import generate_validation_schema, validate_data

asset_dir = join(common.root_dir,
                 'assets/validation-rules/missing-mandatory-column')

parts_v2 = utils.import_dataset(join(asset_dir, 'parts.csv'))
schema_v1 = utils.import_schema(join(asset_dir, 'schema-v1.yml'))
schema_v2 = utils.import_schema(join(asset_dir, 'schema-v2.yml'))

missing_mandatory_column_pass_v1 = {
    'Address': [
        {
            'AddressId': '1',
            'AddL2': 'my street',
        }
    ]
}

missing_mandatory_column_fail_v1 = deepcopy(missing_mandatory_column_pass_v1)
missing_mandatory_column_fail_v1['Address'][0].pop('AddressId')

missing_mandatory_column_pass_v2 = {
    'addresses': utils.import_dataset(join(asset_dir, 'valid-dataset.csv')),
}

missing_mandatory_column_fail_v2 = {
    'addresses': utils.import_dataset(join(asset_dir, 'invalid-dataset.csv')),
}


class TestValidateData(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_schema_generation_v1(self):
        result = generate_validation_schema(parts_v2, schema_version='1.0.0')
        self.assertDictEqual(schema_v1, result)

    def test_schema_generation_v2(self):
        result = generate_validation_schema(parts_v2, schema_version='2.0.0')
        self.assertDictEqual(schema_v2, result)

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
        self.missing_mandatory_column_impl(schema_v1, 'AddressId',
                                           missing_mandatory_column_pass_v1,
                                           missing_mandatory_column_fail_v1)

    def test_missing_mandatory_column_v2(self):
        self.missing_mandatory_column_impl(schema_v2, 'addID',
                                           missing_mandatory_column_pass_v2,
                                           missing_mandatory_column_fail_v2)


if __name__ == '__main__':
    unittest.main()
