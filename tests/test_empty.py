import unittest

from parameterized import parameterized

from odm_validation.schemas import import_schema
from odm_validation.utils import import_dataset, import_json_file
from odm_validation.validation import _validate_data_ext

import common
from common import asset


class TestEmpty(common.OdmTestCase):
    '''tests minlength and allowed together with missing_values_found due to
    anyof-empty constraint'''

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    @parameterized.expand(['allowed', 'minlength'])
    def test_empty(self, rulename: str):
        common.ASSET_SUBDIR = 'validation-rules/empty'
        schema = import_schema(asset(f'schema-v2-{rulename}.yml'))
        data = {'sites': import_dataset(asset(f'dataset-{rulename}.csv'))}
        report = _validate_data_ext(schema, data)
        expected = import_json_file(asset(f'error-report-{rulename}.json'))
        self.assertReportEqual(expected, report)


if __name__ == '__main__':
    unittest.main()
