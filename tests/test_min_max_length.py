import unittest

from parameterized import parameterized, parameterized_class

from odm_validation.rules import RuleId
from odm_validation.schemas import import_schema
from odm_validation.utils import (
    import_dataset,
    import_json_file,
)
from odm_validation.validation import (
    _generate_validation_schema_ext,
    validate_data,
)

import common
from common import asset, param_range


class Assets():
    def __init__(self, ruleId: RuleId):
        rule_dirname = ruleId.name.replace('_', '-')
        common.ASSET_SUBDIR = f'validation-rules/{rule_dirname}'

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
