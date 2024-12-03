import unittest
from os.path import join

from parameterized import parameterized

import common
from common import asset, root_dir
from utils import (
    import_dataset,
    import_schema,
)
from validation import _validate_data_ext


class TestEmpty(common.OdmTestCase):
    '''tests minlength and allowed together with missing_values_found due to
    anyof-empty constraint'''

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    @parameterized.expand(['allowed', 'minlength'])
    def test_empty(self, rulename: str):
        common.ASSET_DIR = join(root_dir, 'assets/validation-rules/empty')
        schema = import_schema(asset(f'schema-v2-{rulename}.yml'))
        data = {'sites': import_dataset(asset(f'dataset-{rulename}.csv'))}
        report = _validate_data_ext(schema, data)
        expected = import_dataset(asset(f'error-report-{rulename}.json'))
        self.assertReportEqual(expected, report)


if __name__ == '__main__':
    unittest.main()
