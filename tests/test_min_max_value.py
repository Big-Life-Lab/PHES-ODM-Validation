import unittest
from os.path import join
# from pprint import pprint

from parameterized import parameterized, parameterized_class

from odm_validation.rules import RuleId
from odm_validation.schemas import import_schema
from odm_validation.stdext import deep_update
from odm_validation.utils import (
    import_dataset,
    import_json_file,
)
from odm_validation.validation import (
    _generate_validation_schema_ext,
    _validate_data_ext,
)

import common
from common import asset, root_dir, param_range


class Assets():
    def __init__(self, ruleId: RuleId):
        rule_dirname = ruleId.name.replace('_', '-')
        common.ASSET_DIR = join(root_dir,
                                f'assets/validation-rules/{rule_dirname}')

        datetime_parts = import_dataset(asset('parts-datetime.csv'))
        datetime_schema_v1 = import_schema(asset('schema-datetime-v1.yml'))
        datetime_schema_v2 = import_schema(asset('schema-datetime-v2.yml'))

        self.parts = (import_dataset(asset('parts.csv')) + datetime_parts)
        self.schemas = {
            1: import_schema(asset('schema-v1.yml')),
            2: import_schema(asset('schema-v2.yml')),
        }
        deep_update(self.schemas[1], datetime_schema_v1)
        deep_update(self.schemas[2], datetime_schema_v2)

        self.data_pass = []
        for i in range(1, 5):
            self.data_pass.append({
                'sites': import_dataset(asset(f'valid-dataset-{i}.*'))
            })
        empty_report = {'errors': [], 'warnings': []}
        self.error_report_pass = [
            empty_report,
            import_json_file(asset('error-report-pass-2.json')),
            empty_report,
            import_json_file(asset('error-report-pass-4.json')),
        ]

        self.data_fail = []
        self.error_report_fail = []
        for i in range(1, 5):
            self.data_fail.append(
                {'sites': import_dataset(asset(f'invalid-dataset-{i}.*'))})
            self.error_report_fail.append(
                import_json_file(asset(f'error-report-{i}.json')))


@parameterized_class([
   {'ruleId': RuleId.less_than_min_value},
   {'ruleId': RuleId.greater_than_max_value},
])
class TestMinMaxValue(common.OdmTestCase):
    ruleId: RuleId

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.ruleId)
        cls.whitelist = [cls.ruleId]

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        result = _generate_validation_schema_ext(
            parts=self.assets.parts,
            schema_version=f'{major_ver}.0.0',
            rule_whitelist=[self.ruleId])
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    @parameterized.expand(param_range(0, 4))
    def test_passing_datasets(self, ix):
        report = _validate_data_ext(self.assets.schemas[2],
                                    self.assets.data_pass[ix],
                                    rule_whitelist=self.whitelist)
        expected = self.assets.error_report_pass[ix]
        self.assertReportEqual(expected, report)

    @parameterized.expand(param_range(0, 4))
    def test_failing_datasets(self, ix):
        report = _validate_data_ext(self.assets.schemas[2],
                                    self.assets.data_fail[ix],
                                    rule_whitelist=self.whitelist)
        expected = self.assets.error_report_fail[ix]
        self.assertReportEqual(expected, report)


class TestMinMaxValueExtra(common.OdmTestCase):
    ruleIds = [RuleId.less_than_min_value, RuleId.greater_than_max_value]

    def test_schema_generation_zero(self):
        # zero is a valid min/max value
        parts = [
            {'partID': 't', 'partType': 'tables', 'status': 'active'},
            {'partID': 'a', 'partType': 'attributes', 't': 'header',
             'dataType': 'integer',
             'minValue': 0, 'maxValue': 0, 'status': 'active'},
        ]
        schema = _generate_validation_schema_ext(
            parts,
            rule_whitelist=self.ruleIds)
        attr_schema = schema['schema']['t']['schema']['schema']['a']
        self.assertEqual(attr_schema['min'], 0)
        self.assertEqual(attr_schema['max'], 0)


if __name__ == '__main__':
    unittest.main()
