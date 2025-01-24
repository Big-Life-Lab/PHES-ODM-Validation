import unittest

from parameterized import parameterized

import odm_validation.odm as odm
from odm_validation.rules import RuleId
from odm_validation.schemas import import_schema
from odm_validation.utils import import_dataset, import_json_file
from odm_validation.validation import (
    _generate_validation_schema_ext,
    _validate_data_ext,
)

import common
from common import asset, gen_v2_testschemas, param_range


class Assets():
    def __init__(self, rule_id: RuleId, table: str):
        rule_dirname = rule_id.name.replace('_', '-')
        common.ASSET_SUBDIR = f'validation-rules/{rule_dirname}'

        # parts
        self.parts = import_dataset(asset('parts.csv'))

        # schemas
        self.schemas = gen_v2_testschemas(import_schema(asset('schema-v2.yml')))
        self.schemas['1.0.0'] = import_schema(asset('schema-v1.yml'))

        # datasets and error reports
        self.data_pass = {table: import_dataset(asset('valid-dataset.csv'))}
        self.data_fail = {}
        self.reports = {}
        for i in range(1, 4):
            self.data_fail[i] = \
                {table: import_dataset(asset(f'invalid-dataset-{i}.csv'))}
            self.reports[i] = import_json_file(asset(f'error-report-{i}.json'))


class TestMissingValuesFound(common.OdmTestCase):
    rule_id = RuleId.missing_values_found
    table = 'sites'

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.rule_id, cls.table)
        cls.whitelist = [cls.rule_id]

    @parameterized.expand(['1.0.0'] + odm.CURRENT_VERSION_STRS)
    def test_schema_generation(self, vstr):
        result = _generate_validation_schema_ext(parts=self.assets.parts,
                                                 schema_version=vstr,
                                                 rule_whitelist=self.whitelist)
        self.assertDictEqual(self.assets.schemas[vstr], result)

    @parameterized.expand(odm.CURRENT_VERSION_STRS)
    def test_passing_datasets(self, vstr):
        report = _validate_data_ext(self.assets.schemas[vstr],
                                    self.assets.data_pass)
        self.assertTrue(report.valid())

    @parameterized.expand(param_range(1, 4))
    def test_failing_datasets(self, i):
        report = _validate_data_ext(schema=self.assets.schemas['2.0.0'],
                                    data=self.assets.data_fail[i])
        expected = self.assets.reports[i]
        self.assertReportEqual(expected, report)


if __name__ == '__main__':
    unittest.main()
