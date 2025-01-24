import unittest

from parameterized import parameterized, parameterized_class

import odm_validation.odm as odm
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
from common import asset, gen_v2_testschemas


class Assets():
    def __init__(self, ruleId: RuleId):
        rule_dirname = ruleId.name.replace('_', '-')
        common.ASSET_SUBDIR = f'validation-rules/{rule_dirname}'

        self.parts_v2 = import_dataset(asset('parts.csv'))
        self.schemas = gen_v2_testschemas(
            import_schema(asset('schema-v2.yml')))
        self.schemas['1.0.0'] = import_schema(asset('schema-v1.yml'))

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

    @parameterized.expand(['1.0.0'] + odm.CURRENT_VERSION_STRS)
    def test_schema_generation(self, vstr):
        result = _generate_validation_schema_ext(
            parts=self.assets.parts_v2,
            schema_version=vstr,
            rule_whitelist=self.whitelist)
        self.assertDictEqual(self.assets.schemas[vstr], result)

    @parameterized.expand(odm.CURRENT_VERSION_STRS)
    def test_pass(self, vstr):
        report = validate_data(self.assets.schemas[vstr],
                               self.assets.data_pass_v2)
        self.assertTrue(report.valid())

    @parameterized.expand(odm.CURRENT_VERSION_STRS)
    def test_fail(self, vstr):
        report = validate_data(self.assets.schemas[vstr],
                               self.assets.data_fail_v2)
        self.assertReportEqual(self.assets.error_report, report)


if __name__ == '__main__':
    unittest.main()
