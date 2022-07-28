# This is a temporary test file to speed up initial development.

import os
import pprint

import utils
import validate
import rules as validation_rules


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


data = {
    "addresses": [
        {
            "addressID": "1",
            # "datasetID": "2",
            "city": "Ottawa",
            "country": "Canada1",
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

# print()
pp = pprint.PrettyPrinter(width=80, compact=True)
sparseParts = fetchParts()
parts = list(map(validate.stripRow, sparseParts))
rules = validation_rules.generate_rules(parts)
schema = validation_rules.generate_cerberus_schema(rules)
# pp.pprint(schema)
errors = validate.validate_data(rules, schema, data)
pp.pprint(errors)
