import unittest

from parameterized import parameterized

from odm_validation.rules import RuleId
from odm_validation.schemas import import_schema
from odm_validation.utils import import_json_file
from odm_validation.validation import _generate_validation_schema_ext

import common
from common import asset, param_range


class Assets():
    def __init__(self):
        common.ASSET_SUBDIR = 'specs/module-functions'

        self.parts = {
            1: import_json_file(asset('parts-1.json')),
            2: import_json_file(asset('parts-2.json'))
        }

        self.sets = {
            1: [],
            2: import_json_file(asset('sets-2.json'))
        }

        self.schema_additions = {
            1: import_json_file(asset('schema-additions-1.json')),
            2: import_json_file(asset('schema-additions-2.json')),
        }

        self.schemas = {
            1: import_schema(asset('schema-1.yml')),
            2: import_schema(asset('schema-2.yml')),
        }


class TestSchemaAdditions(common.OdmTestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.assets = Assets()
        cls.whitelist = [RuleId.invalid_category,
                         RuleId.missing_mandatory_column]

    @parameterized.expand(param_range(1, 3))
    def test_schema_generation(self, i):
        additions = self.assets.schema_additions[i]
        result = _generate_validation_schema_ext(parts=self.assets.parts[i],
                                                 sets=self.assets.sets[i],
                                                 schema_version=f'{i}.0.0',
                                                 schema_additions=additions,
                                                 rule_whitelist=self.whitelist)
        self.assertDictEqual(self.assets.schemas[i], result)


if __name__ == '__main__':
    unittest.main()
