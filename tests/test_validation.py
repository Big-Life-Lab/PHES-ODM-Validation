import pprint
import unittest

import context

from part_tables import Schema
from validation import generate_cerberus_schema, validate_data

context.unused_import_dummy = 1

parts = [
    # missing_mandatory_column parts
    {
        "partID": "addresses",
        "partType": "table",
    },
    {
        "partID": "contacts",
        "partType": "table",
    },
    {
        "partID": "addressID",
        "partType": "attribute",
        "addresses": "PK",
        "addressesRequired": "mandatory",
    },
    {
        "partID": "addL2",
        "partType": "attribute",
        "addresses": "header",
        "addressesRequired": "optional",
    },
    {
        "partID": "contactID",
        "partType": "attribute",
        "contacts": "PK",
    },

    # invalid_category parts
    {
        "partID": "samples",
        "partType": "table",
    },
    {
        "partID": "collection",
        "partType": "attribute",
        "samples": "header",
        "dataType": "categorical",
        "catSetID": "collectCat"
    },
    {
        "partID": "comp3h",
        "partType": "category",
        "samples": "input",
        "dataType": "varchar",
        "catSetID": "collectCat"
    },
    {
        "partID": "comp8h",
        "partType": "category",
        "samples": "input",
        "dataType": "varchar",
        "catSetID": "collectCat"
    },
    {
        "partID": "flowPr",
        "partType": "category",
        "samples": "input",
        "dataType": "varchar",
        "catSetID": "collectCat"
    }
]

missing_mandatory_column_pass = {
    "addresses": [
        {
            "addressID": "1",
            "addL2": "123 Doe Street"
        }
    ]
}

missing_mandatory_column_fail = {
    "addresses": [
        {
            "addL2": "123 Doe Street"
        }
    ]
}

invalid_category_pass = {
    "samples": [
        {
            "collection": "flowPr"
        }
    ]
}

invalid_category_fail = {
    "samples": [
        {
            "collection": "flow"
        }
    ]
}


class TestValiation(unittest.TestCase):
    def setUp(self):
        self.pp = pprint.PrettyPrinter(width=80, compact=True)
        self.schema = generate_cerberus_schema(parts)

    def test_schema(self):
        self.assertIsInstance(self.schema, Schema)
        self.assertNotEqual(self.schema, {})

    def test_missing_mandatory_column(self):
        errors = validate_data(self.schema, missing_mandatory_column_pass)
        self.assertIsNone(errors)
        errors = validate_data(self.schema, missing_mandatory_column_fail)
        self.assertIsNotNone(errors)
        self.assertEqual(len(errors), 1)
        e = errors[0]
        self.assertEqual(e["errorType"], "missing_mandatory_column")
        self.assertEqual(e["columnName"], "addressID")

    def test_invalid_category(self):
        errors = validate_data(self.schema, invalid_category_pass)
        self.assertIsNone(errors)
        errors = validate_data(self.schema, invalid_category_fail)
        self.assertIsNotNone(errors)
        self.assertEqual(len(errors), 1)
        e = errors[0]
        self.assertEqual(e["errorType"], "invalid_category")
        self.assertEqual(e["columnName"], "collection")
        self.assertEqual(e["invalidValue"], "flow")


if __name__ == '__main__':
    unittest.main()
