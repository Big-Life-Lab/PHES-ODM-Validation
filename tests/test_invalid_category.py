import unittest

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
from common import asset


common.ASSET_SUBDIR = 'validation-rules/invalid-category'

parts = import_dataset(asset('parts.csv'))
sets = import_dataset(asset('sets.csv'))
schema_v1 = import_schema(asset('schema-v1.yml'))
schema_v2 = import_schema(asset('schema-v2.yml'))
error_report = import_json_file(asset('error-report.json'))

invalid_category_pass_1_v2 = {
    'samples': import_dataset(asset('valid-dataset-1.csv')),
}

invalid_category_pass_2_v2 = {
    'samples': import_dataset(asset('valid-dataset-2.csv')),
}

invalid_category_fail_v2 = {
    'samples': import_dataset(asset('invalid-dataset.csv')),
}


class TestInvalidCategory(common.OdmTestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.whitelist = [RuleId.invalid_category]

    def test_schema_generation_v1(self):
        # XXX: The part 'tp24s' should not be included, since it doesn't belong
        # to an attribute. It's only in the parts as a negative example.
        result = _generate_validation_schema_ext(
            parts=parts,
            schema_version='1.0.0',
            rule_whitelist=self.whitelist)
        self.assertDictEqual(schema_v1, result)

    def test_schema_generation_v2(self):
        result = _generate_validation_schema_ext(
            parts=parts,
            sets=sets,
            schema_version='2.0.0',
            rule_whitelist=self.whitelist)
        got = result['schema']['samples']
        expected = schema_v2['schema']['samples']
        self.assertDictEqual(expected, got)

    def test_invalid_category_v2(self):
        report = validate_data(schema_v2, invalid_category_pass_1_v2)
        self.assertTrue(report.valid())

        report = validate_data(schema_v2, invalid_category_pass_1_v2)
        self.assertTrue(report.valid())

        report = validate_data(schema_v2, invalid_category_fail_v2)
        expected = error_report
        self.assertEqual(report.errors, expected['errors'])


if __name__ == '__main__':
    unittest.main()
