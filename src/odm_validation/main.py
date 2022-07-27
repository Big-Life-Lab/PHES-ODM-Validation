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


pp = pprint.PrettyPrinter(width=80, compact=True)

parts = fetchParts()
schema = validate.generate_cerberus_schema(parts)
pp.pprint(schema)

data = {
    "addresses": [
        {
            "addressID": "1",
            # "datasetID": "2",
            "city": "Ottawa",
            "country": "Canada",
        },
        {
            # "addressID": "2",
            "datasetID": "2",
            "city": "Ottawa",
            "country": "Canada",
            "addL2": "12345 Lane Avenue",
        }
    ],
    "contacts": [
        {
            # "contactID": "1",
            "organizationID": "1",
        }
    ]
}

print()
errors = validate.validate_data(schema, data)
pp.pprint(errors)
