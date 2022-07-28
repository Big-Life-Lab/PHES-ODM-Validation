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


def get_table_attributes(table_names, attributes) -> dict:
    """Returns dict of table names and their attribute parts."""
    result = {}
    for t in table_names:
        result[t] = []
    for a in attributes:
        assert type(a) is dict
        for t in table_names:
            if a.get(t):
                result[t].append(a)
    return result


def generate_rules(parts):
    tables = list(filter(lambda x: x.get("partType") == "table", parts))
    table_names = [row["partID"] for row in tables]
    attributes = list(filter(lambda x: x.get("partType") == "attribute", parts))
    table_attr = get_table_attributes(table_names, attributes)

    rules = []
    for t in table_names:
        a = table_attr[t]
        r = validation_rules.missing_mandatory_column(t, a)
        rules.append(r)
    return rules


def generate_cerberus_schema(rules):
    schema = {}
    for r in rules:
        if r.schema:
            schema.update(r.schema)
    return schema


pp = pprint.PrettyPrinter(width=80, compact=True)
sparseParts = fetchParts()
parts = list(map(validate.stripRow, sparseParts))
rules = generate_rules(parts)
schema = generate_cerberus_schema(rules)
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

# print()
# errors = validate.validate_data(schema, data)
# pp.pprint(errors)
