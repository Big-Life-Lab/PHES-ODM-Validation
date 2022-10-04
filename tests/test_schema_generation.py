import logging
import os
import sys
import unittest
from copy import deepcopy
from os.path import join
from pprint import pprint

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
    # {
    #     "partID": "contacts",
    #     "partType": "table",
    #     "version1Location": "tables",
    #     "verion1Table": "Contact",
    # },
    {
        "partID": "addID",
        "partType": "attribute",
        "addresses": "PK",
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
    # {
    #     "partID": "contactID",
    #     "partType": "attribute",
    #     "contacts": "PK",
    #     "version1Location": "variables",
    #     "verion1Table": "Contact",
    #     "version1Variable": "contactID"
    # }
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
                                    "addresses": "PK",  # not in spec
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
    # "Contact": {
    #     "type": "list",
    #     "schema": {
    #         "type": "dict",
    #         "schema": {
    #             "contactID": {
    #                 "required": True,
    #                 "meta": [
    #                     {
    #                         "ruleId": "missing_mandatory_column",
    #                         "meta": [
    #                             {
    #                                 "partID": "contactID",
    #                                 "contactsRequired": "mandatory",
    #                                 "version1Location": "variables",
    #                                 "verion1Table": "Contact",
    #                                 "version1Variable": "contactID"
    #                             }
    #                         ]
    #                     }
    #                 ]
    #             }
    #         }
    #     },
    #     "meta": {
    #         "partID": "contacts",
    #         "partType": "table",
    #         "version1Location": "tables",
    #         "verion1Table": "Contact"
    #     }
    # }
}


class TestGenerateValidationSchema(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.maxDiff = None  # disable assert diff length limitation

    def test_(self):
        schema = generate_validation_schema(parts_v2, schema_version="1")
        pprint(schema)
        self.assertDictEqual(expected_cerb_schema_v1, schema["schema"])


if __name__ == '__main__':
    unittest.main()
