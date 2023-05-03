import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized, parameterized_class

import common
from common import asset, root_dir, param_range
from rules import RuleId
from utils import (
    import_dataset,
    import_json_file,
    import_schema,
)
from validation import _generate_validation_schema_ext, validate_data


class Assets():
    def __init__(self, ruleId: RuleId):
        rule_dirname = ruleId.name.replace('_', '-')
        common.ASSET_DIR = join(root_dir,
                                f'assets/validation-rules/{rule_dirname}')

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
   {'ruleId': RuleId.less_than_min_length},
   {'ruleId': RuleId.greater_than_max_length},
])
class TestMinMaxLength(common.OdmTestCase):
    ruleId: RuleId

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.ruleId)
        cls.whitelist = [cls.ruleId]

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        result = _generate_validation_schema_ext(
            parts=self.assets.parts_v2,
            schema_version=f'{major_ver}.0.0',
            rule_whitelist=self.whitelist)
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    def test_pass(self):
        report = validate_data(self.assets.schemas[2],
                               self.assets.data_pass_v2)
        self.assertTrue(report.valid())

    def test_fail(self):
        report = validate_data(self.assets.schemas[2],
                               self.assets.data_fail_v2)
        self.assertReportEqual(self.assets.error_report, report)


if __name__ == '__main__':
    unittest.main()
