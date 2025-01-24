import unittest

from parameterized import parameterized

import odm_validation.odm as odm
from odm_validation.rules import RuleId
from odm_validation.schemas import import_schema
from odm_validation.utils import import_dataset, import_json_file
from odm_validation.validation import (
    _generate_validation_schema_ext,
    validate_data,
)

import common
from common import asset, gen_v2_testschemas


common.ASSET_SUBDIR = 'validation-rules/missing-mandatory-column'

parts_v2 = import_dataset(asset('parts.csv'))
schema_v1 = import_schema(asset('schema-v1.yml'))
v2_schema = import_schema(asset('schema-v2.yml'))
v2_schemas = gen_v2_testschemas(v2_schema)
error_report = import_json_file(asset('error-report.json'))

missing_mandatory_column_pass_v2 = {
    'addresses': import_dataset(asset('valid-dataset.csv')),
}

missing_mandatory_column_fail_v2 = {
    'addresses': import_dataset(asset('invalid-dataset.csv')),
}


class TestMissingMandatoryColumn(common.OdmTestCase):
    rule_id = RuleId.missing_mandatory_column

    def setUp(self):
        self.maxDiff = None
        self.whitelist = [self.rule_id]

    def test_schema_generation_v1(self):
        result = _generate_validation_schema_ext(parts=parts_v2,
                                                 schema_version='1.0.0',
                                                 rule_whitelist=self.whitelist)
        self.assertDictEqual(schema_v1, result)

    @parameterized.expand(odm.CURRENT_VERSION_STRS)
    def test_schema_generation_v2(self, vstr):
        result = _generate_validation_schema_ext(parts=parts_v2,
                                                 schema_version=vstr,
                                                 rule_whitelist=self.whitelist)
        self.assertDictEqual(v2_schemas[vstr], result)

    @parameterized.expand(odm.CURRENT_VERSION_STRS)
    def test_missing_mandatory_column_v2(self, vstr):
        schema = v2_schemas[vstr]
        report = validate_data(schema, missing_mandatory_column_pass_v2)
        self.assertTrue(report.valid())
        report = validate_data(schema, missing_mandatory_column_fail_v2)
        expected = error_report
        self.assertEqual(report.errors, expected['errors'])


if __name__ == '__main__':
    unittest.main()
