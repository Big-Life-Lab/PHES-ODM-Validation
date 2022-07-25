# This is a temporary test file to speed up initial development.

import os
import pprint

import utils
import validate


def fetchParts() -> [dict]:
    xlsxOdm = "odm-v1.1.xlsx"
    xlsxOdmSheet = "parts"
    # xlsxOdmUrl = "https://osf.io/download/k94qe/"
    csvSchema = f"odm-{xlsxOdmSheet}.csv"

    # if not os.path.isfile(xlsxOdm):
    #     utils.downloadFile(xlsxOdmUrl, xlsxOdm)
    if not os.path.isfile(csvSchema):
        utils.convertXlsx2Csv(xlsxOdm, xlsxOdmSheet, csvSchema)
    return utils.importCsvFile(csvSchema)


parts = fetchParts()
schema = validate.generate_cerberus_schema(parts)
pp = pprint.PrettyPrinter(width=80, compact=True)
pp.pprint(schema)

schema = {
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
                    "required": True,
                    "meta": {
                        "partID": "addressID",
                        "addresses": "PK",
                        "addressesRequired": "mandatory",
                    }
                },
                "addL2": {
                    "meta": {
                        "partID": "contactID",
                        "contacts": "PK",
                        "contactsRequired": "NA"
                    }
                }
            },
            "meta": {
                "partID": "addresses",
                "partType": "table"
            }
        }
    },
    "contacts": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "contactID": {
                    "required": True,
                    "meta": {
                        "partID": "contactID",
                        "ContactTable": "PK",
                        "ContactTableRequired": "mandatory"
                    }
                }
            }
        },
        "meta": {
            "partID": "contacts",
            "partType": "table"
        }
    }
}

data = {
    "addresses": [
        {
            "addressID": "1",
        },
        {
            "addL2": "12345 Lane Avenue"
        }
    ],
    "contacts": [
        {
            "contactID": "1"
        }
    ]
}

print()
errors = validate.validate_data(schema, data)
pp.pprint(errors)
