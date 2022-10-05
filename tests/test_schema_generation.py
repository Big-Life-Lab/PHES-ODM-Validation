import logging
import os
import sys
import unittest
from copy import deepcopy
from os.path import join

import context

import utils
from part_tables import Schema
from validation import generate_validation_schema

context.unused_import_dummy = 1

parts_v2 = [
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
        "version1Variable": "addressID"
    },
    {
        "partID": "addL2",
        "partType": "attribute",
        "addresses": "header",
        "addressesRequired": "optional",
        "version1Location": "variables",
        "version1Table": "Address",
        "version1Variable": "addressLineTwo"
    },
    {
        "partID": "contID",
        "partType": "attribute",
        "contacts": "pK",
        "contactsRequired": "mandatory",
        "version1Location": "variables",
        "version1Table": "Contact",
        "version1Variable": "contactID"
    }
]

expected_cerb_schema_v1 = {
    "Address": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
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
                                    "version1Variable": "addressID"
                                }
                            ]
                        }
                    ]
                },
            },
            "meta": {
                "partID": "addresses",
                # "partType": "table",  # in spec, but excluded
                "version1Location": "tables",
                "version1Table": "Address"
            }
        }
    },
    "Contact": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "contactID": {
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
                                    "version1Variable": "contactID"
                                }
                            ]
                        }
                    ]
                }
            },
            "meta": {
                "partID": "contacts",
                # "partType": "table",  # in spec, but excluded
                "version1Table": "Contact",
                "version1Location": "tables",
            }
        },
    }
}


class TestGenerateValidationSchema(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.maxDiff = None  # disable assert diff length limitation

    def test_(self):
        schema = generate_validation_schema(parts_v2, schema_version="1")
        self.assertDictEqual(expected_cerb_schema_v1, schema["schema"])


if __name__ == '__main__':
    unittest.main()
