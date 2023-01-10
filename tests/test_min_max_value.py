import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized, parameterized_class

import common
from utils import (
    import_dataset,
    import_json_file,
    import_schema,
    import_yaml_file
)
from validation import generate_validation_schema, validate_data


def _param_range(start, stop):
    return list(map(lambda i: (i, ), range(start, stop)))


class Assets():
    def __init__(self, ruleId: str):
        rule_dirname = ruleId.replace('_', '-')
        asset_dir = join(common.root_dir,
                         f'assets/validation-rules/{rule_dirname}')

        def asset(filename: str) -> str:
            return join(asset_dir, filename)

        self.parts_v2 = import_dataset(asset('parts.csv'))
        self.schemas = {
            1: import_schema(asset('schema-v1.yml')),
            2: import_schema(asset('schema-v2.yml')),
        }

        self.data_pass_v2 = [
            {'sites': import_dataset(asset('valid-dataset-1.yml'))},
            {'sites': import_dataset(asset('valid-dataset-2.csv'))},
            {'sites': import_dataset(asset('valid-dataset-3.yml'))},
        ]

        self.data_fail_v2 = [
            {'sites': import_yaml_file(asset('invalid-dataset-1.yml'))},
            {'sites': import_dataset(asset('invalid-dataset-2.csv'))},
            {'sites': import_dataset(asset('invalid-dataset-3.csv'))},
        ]

        self.error_report_fail = [
            import_json_file(asset('error-report-1.json')),
            import_json_file(asset('error-report-2.json')),
            import_json_file(asset('error-report-3.json')),
        ]

        empty_report = {'errors': [], 'warnings': []}
        self.error_report_pass = [
            empty_report,
            import_json_file(asset('error-report-4.json')),
            empty_report,
        ]


@parameterized_class([
   {'ruleId': 'less_than_min_value'},
   {'ruleId': 'greater_than_max_value'},
])
class TestMinMaxValue(unittest.TestCase):
    ruleId: str

    def setUp(self):
        self.maxDiff = None
        self.assets = Assets(self.ruleId)

    @parameterized.expand(_param_range(1, 3))
    def test_schema_generation(self, major_ver):
        result = generate_validation_schema(self.assets.parts_v2,
                                            schema_version=f'{major_ver}.0.0')
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    def _assertEqual(self, report, expected):
        self.assertEqual(report.errors, expected['errors'])
        self.assertEqual(report.warnings, expected['warnings'])

    @parameterized.expand(_param_range(0, 3))
    def test_passing_datasets(self, ix):
        report = validate_data(self.assets.schemas[2],
                               self.assets.data_pass_v2[ix])
        expected = self.assets.error_report_pass[ix]
        self._assertEqual(report, expected)

    @parameterized.expand(_param_range(0, 3))
    def test_failing_datasets(self, ix):
        report = validate_data(self.assets.schemas[2],
                               self.assets.data_fail_v2[ix])
        expected = self.assets.error_report_fail[ix]
        self._assertEqual(report, expected)


if __name__ == '__main__':
    unittest.main()
