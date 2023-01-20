import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized, parameterized_class

from common import root_dir, param_range
from utils import (
    import_dataset,
    import_json_file,
    import_schema,
)
from validation import generate_validation_schema, validate_data


class Assets():
    def __init__(self, ruleId: str):
        rule_dirname = ruleId.replace('_', '-')
        asset_dir = join(root_dir,
                         f'assets/validation-rules/{rule_dirname}')

        def asset(filename: str) -> str:
            return join(asset_dir, filename)

        self.parts_v2 = import_dataset(asset('parts.csv'))
        self.schemas = {
            1: import_schema(asset('schema-v1.yml')),
            2: import_schema(asset('schema-v2.yml')),
        }

        self.data_pass_v2 = {
            'contacts': import_dataset(asset('valid-dataset.csv')),
        }

        self.data_fail_v2 = {
            'contacts': import_dataset(asset('invalid-dataset.csv'))
        }

        self.error_report = import_json_file(asset('error-report.json'))


@parameterized_class([
   {'ruleId': 'less_than_min_length'},
   {'ruleId': 'greater_than_max_length'},
])
class TestMinMaxLength(unittest.TestCase):
    ruleId: str

    def setUp(self):
        self.maxDiff = None
        self.assets = Assets(self.ruleId)

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        result = generate_validation_schema(self.assets.parts_v2,
                                            schema_version=f'{major_ver}.0.0')
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    def _assertEqual(self, report, expected):
        self.assertEqual(report.errors, expected['errors'])
        self.assertEqual(report.warnings, expected['warnings'])

    def test_pass(self):
        report = validate_data(self.assets.schemas[2],
                               self.assets.data_pass_v2)
        self.assertTrue(report.valid())

    def test_fail(self):
        report = validate_data(self.assets.schemas[2],
                               self.assets.data_fail_v2)
        self._assertEqual(report, self.assets.error_report)


if __name__ == '__main__':
    unittest.main()
