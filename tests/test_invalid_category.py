import os
import unittest
from copy import deepcopy
from os.path import join

import common

import utils
from validation import generate_validation_schema, validate_data


parts_v2 = [
    {
        "partID": "samples",
        "partType": "table",
        "version1Location": "tables",
        "version1Table": "Sample",
    },
    {
        "partID": "coll",
        "partType": "attribute",
        "samples": "header",
        "dataType": "categorical",
        "catSetID": "collectCat",
        "version1Location": "variables",
        "version1Table": "Sample",
        "version1Variable": "Collection",
    },
    {
        "partID": "comp3h",
        "partType": "category",
        "samples": "input",
        "dataType": "varchar",
        "catSetID": "collectCat",
        "version1Location": "variableCategories",
        "version1Table": "Sample",
        "version1Variable": "Collection",
        "version1Category": "Comp3h"
    },
    {
        "partID": "comp8h",
        "partType": "category",
        "samples": "input",
        "dataType": "varchar",
        "catSetID": "collectCat",
        "version1Location": "variableCategories",
        "version1Table": "Sample",
        "version1Variable": "Collection",
        "version1Category": "Comp8h"
    },
    {
        "partID": "flowPr",
        "partType": "category",
        "samples": "input",
        "dataType": "varchar",
        "catSetID": "collectCat",
        "version1Location": "variableCategories",
        "version1Table": "Sample",
        "version1Variable": "Collection",
        "version1Category": "FlowPr; FlowRatePr"
    }
]

schema_v2 = common.import_schema_v2()

schema_v1 = {
    "schemaVersion": "1.0.0",
    "schema": {
        "Sample": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "Collection": {
                        # "type": "string",
                        "allowed": ["Comp3h", "Comp8h", "FlowPr", "FlowRatePr"],
                        "meta": [
                            {
                                "ruleID": "invalid_category",
                                "meta": [
                                    {
                                        "partID": "coll",
                                        "samples": "header",
                                        # "dataType": "categorical",
                                        "catSetID": "collectCat",
                                        "version1Location": "variables",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection"
                                    },
                                    {
                                        "partID": "comp3h",
                                        # "partType": "category",
                                        "catSetID": "collectCat",
                                        "version1Location": "variableCategories",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection",
                                        "version1Category": "Comp3h"
                                    },
                                    {
                                        "partID": "comp8h",
                                        # "partType": "category",
                                        "catSetID": "collectCat",
                                        "version1Location": "variableCategories",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection",
                                        "version1Category": "Comp8h"
                                    },
                                    {
                                        "partID": "flowPr",
                                        # "partType": "category",
                                        "catSetID": "collectCat",
                                        "version1Location": "variableCategories",
                                        "version1Table": "Sample",
                                        "version1Variable": "Collection",
                                        "version1Category": "FlowPr; FlowRatePr"
                                    },
                                ]
                            }
                        ]
                    }
                },
                "meta": [
                    {
                        "partID": "samples",
                        # "partType": "table",
                        "version1Location": "tables",
                        "version1Table": "Sample"
                    }
                ]
            }
        }
    }
}

dir = os.path.dirname(os.path.realpath(__file__))
path = join(dir, '../assets/validation-schemas/schema-v2.0.0-rc.1.yml')
schema_v2 = utils.import_schema(path)

invalid_category_pass_v1 = {
    'Sample': [
        {
            'Collection': 'FlowPr',
        }
    ]
}

invalid_category_pass_v2 = {
    'samples': [
        {
            'coll': 'flowPr',
            'cDT': 'x',
            'saMaterial': 'afu',
            'sampID': '1',
            'siteID': '1',
            'parSampID': '1',
            'dataID': '1',
            'contID': '1',
            'collPer': 'x',
            'collNum': 'x',
        }
    ]
}

invalid_category_fail_v1 = deepcopy(invalid_category_pass_v1)
invalid_category_fail_v1['Sample'][0]['Collection'] = 'flow'

invalid_category_fail_v2 = deepcopy(invalid_category_pass_v2)
invalid_category_fail_v2['samples'][0]['coll'] = 'flow'


class TestInvalidCategory(unittest.TestCase):
    def test_schema_generation_v1(self):
        result = generate_validation_schema(parts_v2, schema_version="1.0.0")
        self.assertDictEqual(schema_v1, result)

    def invalid_category_impl(self, schema, invalid_value_column,
                              invalid_value, data_pass, data_fail):
        report = validate_data(schema, data_pass)
        self.assertTrue(report.valid())
        report = validate_data(schema, data_fail)
        self.assertFalse(report.valid(), report.errors)
        self.assertEqual(len(report.errors), 1)
        e = report.errors[0]
        self.assertEqual(e['errorType'], 'invalid_category')
        self.assertEqual(e['columnName'], invalid_value_column)
        self.assertEqual(e['invalidValue'], invalid_value)

    def test_invalid_category_v1(self):
        self.invalid_category_impl(schema_v1, 'Collection', 'flow',
                                   invalid_category_pass_v1,
                                   invalid_category_fail_v1)

    def test_invalid_category_v2(self):
        self.invalid_category_impl(schema_v2, 'coll', 'flow',
                                   invalid_category_pass_v2,
                                   invalid_category_fail_v2)


if __name__ == '__main__':
    unittest.main()
