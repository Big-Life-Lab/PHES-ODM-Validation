import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized

import common
from common import asset, root_dir, param_range
from rules import RuleId
from utils import (
    import_dataset,
    import_schema,
)
from validation import _generate_validation_schema_ext, _validate_data_ext


class Assets():
    def __init__(self, rule_id: RuleId, table: str):
        rule_dirname = rule_id.name.replace('_', '-')
        common.ASSET_DIR = join(root_dir,
                                f'assets/validation-rules/{rule_dirname}')

        # parts
        self.parts = import_dataset(asset('parts.csv'))

        # schemas
        self.schemas = {
            1: import_schema(asset('schema-v1.yml')),
            2: import_schema(asset('schema-v2.yml')),
        }

        # datasets and error reports
        self.data_pass = {table: import_dataset(asset('valid-dataset.*'))}
        self.data_fail = {}
        self.reports = {}
        for i in range(1, 4):
            self.data_fail[i] = \
                {table: import_dataset(asset(f'invalid-dataset-{i}.*'))}
            self.reports[i] = import_dataset(asset(f'error-report-{i}.json'))


class TestMissingValuesFound(common.OdmTestCase):
    rule_id = RuleId.missing_values_found
    table = 'sites'

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.rule_id, cls.table)
        cls.whitelist = [cls.rule_id]

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        ver = f'{major_ver}.0.0'
        result = _generate_validation_schema_ext(parts=self.assets.parts,
                                                 schema_version=ver,
                                                 rule_whitelist=self.whitelist)
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    def test_passing_datasets(self):
        report = _validate_data_ext(self.assets.schemas[2],
                                    self.assets.data_pass)
        self.assertTrue(report.valid())

    @parameterized.expand(param_range(1, 4))
    def test_failing_datasets(self, i):
        report = _validate_data_ext(schema=self.assets.schemas[2],
                                    data=self.assets.data_fail[i])
        expected = self.assets.reports[i]
        self.assertReportEqual(expected, report)


if __name__ == '__main__':
    unittest.main()
