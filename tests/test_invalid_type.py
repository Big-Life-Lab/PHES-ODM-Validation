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
    _validate_data_ext,
)

import common
from common import asset, import_dataset2, param_range


class Assets():
    def __init__(self, rule_id: RuleId, kind: str, table: str):
        rule_dirname = rule_id.name.replace('_', '-')
        common.ASSET_SUBDIR = f'validation-rules/{rule_dirname}'

        self.parts_v2 = import_dataset(asset(f'{kind}-parts.csv'))
        self.sets = (import_dataset(asset('bool-sets.csv')) if kind == 'bool'
                     else [])

        self.schemas = {
            1: import_schema(asset(f'{kind}-schema-v1.yml')),
            2: import_schema(asset(f'{kind}-schema-v2.yml')),
        }

        # datasets
        # TODO: glob all files instead of hardcoding them like this?
        self.data_pass = [
            {table: import_dataset2(asset(f'{kind}-valid-dataset-1.*'))},
        ]
        self.data_fail = [
            {table: import_dataset2(asset(f'{kind}-invalid-dataset-1.*'))},
        ]
        if kind in {'float', 'integer'}:
            self.data_pass.append(
                {table: import_dataset2(asset(f'{kind}-valid-dataset-2.*'))})
        if kind in {'bool', 'integer'}:
            self.data_fail.append(
                {table: import_dataset2(asset(f'{kind}-invalid-dataset-2.*'))})

        # error reports
        self.error_report = [
            import_json_file(asset(f'{kind}-error-report-1.json')),
        ]
        if kind in {'bool', 'integer'}:
            self.error_report.append(
                import_json_file(asset(f'{kind}-error-report-2.json')))


@parameterized_class([
    {'kind': 'bool', 'table': 'measures'},
    {'kind': 'datetime', 'table': 'measures'},
    {'kind': 'float', 'table': 'sites'},
    {'kind': 'integer', 'table': 'sites'},
])
class TestInvalidType(common.OdmTestCase):
    rule_id = RuleId.invalid_type
    kind: str  # asset datatype name
    table: str  # asset table name

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets(cls.rule_id, cls.kind, cls.table)
        cls.whitelist = [cls.rule_id]

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, major_ver):
        # XXX: bool parts were introduced in v1.1
        if self.kind == 'bool' and major_ver == 1:
            ver = '1.1.0'
        else:
            ver = f'{major_ver}.0.0'
        result = _generate_validation_schema_ext(parts=self.assets.parts_v2,
                                                 sets=self.assets.sets,
                                                 schema_version=ver,
                                                 rule_whitelist=self.whitelist)
        self.assertDictEqual(self.assets.schemas[major_ver], result)

    @parameterized.expand(param_range(0, 2))
    def test_passing_datasets(self, i):
        if i < len(self.assets.data_pass):
            report = _validate_data_ext(self.assets.schemas[2],
                                        self.assets.data_pass[i])
            self.assertTrue(report.valid())

    @parameterized.expand(param_range(0, 2))
    def test_failing_datasets(self, i):
        if i < len(self.assets.data_fail):
            report = _validate_data_ext(schema=self.assets.schemas[2],
                                        data=self.assets.data_fail[i])
            expected = self.assets.error_report[i]
            self.assertReportEqual(expected, report)


if __name__ == '__main__':
    unittest.main()
