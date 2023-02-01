import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized

import common
from common import asset, root_dir, param_range
from utils import (
    import_dataset,
    import_json_file,
    import_schema,
)
from validation import generate_validation_schema, _validate_data_ext


class Assets():
    def __init__(self, rule_id: str, table: str):
        rule_dirname = rule_id.replace('_', '-')
        common.ASSET_DIR = join(root_dir,
                                f'assets/validation-rules/{rule_dirname}')

        # parts
        self.parts = import_dataset(asset('parts.csv'))

        # schemas
        self.schemas = {
            1: import_schema(asset('schema-v1.yml')),
            2: import_schema(asset('schema-v2.yml')),
        }

        # datasets
        self.data_pass = {table: import_dataset(asset('valid-dataset.*'))}
        self.data_fail = {
            1: {table: import_dataset(asset('invalid-dataset-1.*'))},
            2: {table: import_dataset(asset('invalid-dataset-2.*'))},
        }

        # error reports
        self.error_report = {
            1: import_json_file(asset('error-report-1.json')),
            2: import_json_file(asset('error-report-2.json'))
        }


class TestDuplicateEntriesFound(common.OdmTestCase):
    rule_id = 'duplicate_entries_found'
    table = 'addresses'

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.rule_id, cls.table)

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        result = generate_validation_schema(self.assets.parts,
                                            schema_version=f'{major_ver}.0.0')
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    def _assertEqual(self, expected, report):
        self.assertEqual(expected['errors'], report.errors)
        self.assertEqual(expected['warnings'], report.warnings)

    def test_passing_datasets(self):
        report = _validate_data_ext(self.assets.schemas[2],
                                    self.assets.data_pass)
        self.assertTrue(report.valid())

    @parameterized.expand(param_range(1, 3))
    def test_failing_datasets(self, i):
        report = _validate_data_ext(schema=self.assets.schemas[2],
                                    data=self.assets.data_fail[i])
        expected = self.assets.error_report[i]
        self._assertEqual(expected, report)


if __name__ == '__main__':
    unittest.main()
