import logging
import unittest

import context
from validation import generate_validation_schema

context.unused_import_dummy = 1

# v1 variable names may not be accurate, they are only for testing purposes
parts_v2 = [
    # missing_mandatory_column
    {
        "partID": "addresses",
        "partType": "table",
        "version1Location": "tables",
        "version1Table": "Address",
    },
    {
        "partID": "contacts",
        "partType": "table",
        "version1Location": "tables",
        "version1Table": "Contact",
    },
    {
        "partID": "addID",
        "partType": "attribute",
        "addresses": "pK",
        "addressesRequired": "mandatory",
        "version1Location": "variables",
        "version1Table": "Address",
        "version1Variable": "AddressID"
    },
    {
        "partID": "addL2",
        "partType": "attribute",
        "addresses": "header",
        "addressesRequired": "optional",
        "version1Location": "variables",
        "version1Table": "Address",
        "version1Variable": "AddressLineTwo"
    },
    {
        "partID": "contID",
        "partType": "attribute",
        "contacts": "pK",
        "contactsRequired": "mandatory",
        "version1Location": "variables",
        "version1Table": "Contact",
        "version1Variable": "ContactID"
    },

    # invalid_category
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

expected_cerb_schema_v1 = {
    # missing_mandatory_column
    "Address": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "AddressID": {
                    "required": True,
                    "meta": [
                        {
                            "ruleID": "missing_mandatory_column",
                            "meta": [
                                {
                                    "addresses": "pK",  # not in spec
                                    "addressesRequired": "mandatory",
                                    "partID": "addID",
                                    "version1Table": "Address",
                                    "version1Location": "variables",
                                    "version1Variable": "AddressID"
                                }
                            ]
                        }
                    ]
                },
            },
            "meta": [
                {
                    "partID": "addresses",
                    # "partType": "table",
                    "version1Location": "tables",
                    "version1Table": "Address"
                }
            ]
        }
    },
    "Contact": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "ContactID": {
                    "required": True,
                    "meta": [
                        {
                            "ruleID": "missing_mandatory_column",
                            "meta": [
                                {
                                    "contacts": "pK",  # not in spec
                                    "contactsRequired": "mandatory",
                                    "partID": "contID",
                                    "version1Table": "Contact",
                                    "version1Location": "variables",
                                    "version1Variable": "ContactID"
                                }
                            ]
                        }
                    ]
                }
            },
            "meta": [
                {
                    "partID": "contacts",
                    # "partType": "table",
                    "version1Table": "Contact",
                    "version1Location": "tables",
                }
            ]
        },
    },

    # invalid_category
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
                                    # "catSetID": "collectCat",
                                    "version1Location": "variableCategories",
                                    "version1Table": "Sample",
                                    # "version1Variable": "Collection",
                                    "version1Category": "Comp3h"
                                },
                                {
                                    "partID": "comp8h",
                                    # "partType": "category",
                                    # "catSetID": "collectCat",
                                    "version1Location": "variableCategories",
                                    "version1Table": "Sample",
                                    # "version1Variable": "Collection",
                                    "version1Category": "Comp8h"
                                },
                                {
                                    "partID": "flowPr",
                                    # "partType": "category",
                                    # "catSetID": "collectCat",
                                    "version1Location": "variableCategories",
                                    "version1Table": "Sample",
                                    # "version1Variable": "Collection",
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


class TestGenerateValidationSchema(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.maxDiff = None  # disable assert diff length limitation

    def test_(self):
        schema = generate_validation_schema(parts_v2, schema_version="1")
        # pprint(schema)
        self.assertDictEqual(expected_cerb_schema_v1, schema["schema"])


if __name__ == '__main__':
    unittest.main()
