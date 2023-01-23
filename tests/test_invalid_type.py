import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized, parameterized_class

import common
from common import asset, root_dir, param_range
from utils import (
    import_dataset,
    import_json_file,
    import_schema,
)
from validation import generate_validation_schema, _validate_data_ext


class Assets():
    def __init__(self, rule_id: str, kind: str, table: str):
        rule_dirname = rule_id.replace('_', '-')
        common.ASSET_DIR = join(root_dir,
                                f'assets/validation-rules/{rule_dirname}')

        self.parts_v2 = import_dataset(asset(f'{kind}-parts.csv'))
        self.schemas = {
            1: import_schema(asset(f'{kind}-schema-v1.yml')),
            2: import_schema(asset(f'{kind}-schema-v2.yml')),
        }

        # datasets
        # TODO: glob all files instead of hardcoding them like this?
        self.data_pass = [
            {table: import_dataset(asset(f'valid-{kind}-dataset-1.*'))},
        ]
        self.data_fail = [
            {table: import_dataset(asset(f'invalid-{kind}-dataset-1.*'))},
        ]
        if kind in {'float', 'integer'}:
            self.data_pass.append(
                {table: import_dataset(asset(f'valid-{kind}-dataset-2.*'))})
        if kind in {'bool', 'integer'}:
            self.data_fail.append(
                {table: import_dataset(asset(f'invalid-{kind}-dataset-2.*'))})

        # error reports
        self.error_report = [
            import_json_file(asset(f'{kind}-error-report-1.json')),
        ]
        if kind in {'bool', 'integer'}:
            self.error_report.append(
                import_json_file(asset(f'{kind}-error-report-2.json')))


@parameterized_class([
    {'kind': 'bool', 'table': 'measures'},
    {'kind': 'datetime', 'table': 'measures'},
    {'kind': 'float', 'table': 'sites'},
    {'kind': 'integer', 'table': 'sites'},
])
class TestInvalidType(common.OdmTestCase):
    rule_id = 'invalid_type'
    kind: str  # asset datatype name
    table: str  # asset table name

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.rule_id, cls.kind, cls.table)

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        result = generate_validation_schema(self.assets.parts_v2,
                                            schema_version=f'{major_ver}.0.0')
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    def _assertEqual(self, expected, report):
        self.assertEqual(expected['errors'], report.errors)
        self.assertEqual(expected['warnings'], report.warnings)

    @parameterized.expand(param_range(0, 2))
    def test_passing_datasets(self, i):
        if i < len(self.assets.data_pass):
            report = _validate_data_ext(self.assets.schemas[2],
                                        self.assets.data_pass[i])
            self.assertTrue(report.valid())

    @parameterized.expand(param_range(0, 2))
    def test_failing_datasets(self, i):
        if i < len(self.assets.data_fail):
            report = _validate_data_ext(schema=self.assets.schemas[2],
                                        data=self.assets.data_fail[i])
            expected = self.assets.error_report[i]
            self._assertEqual(expected, report)


if __name__ == '__main__':
    unittest.main()