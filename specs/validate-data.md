# Function Signature

## Arguments

The function should accept two arguments, the ODM data to be validated and a cerberus schema which contains the validation rules.

1. The ODM data to be validated is a [dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) whose keys are the table names and values are the table rows represented as a [list](https://developers.google.com/edu/python/lists) of dictionaries. For each dictionary within the list, the keys are the column names and values are the column values. For example, the data argument for a dataset consisting of the Address and Contact table can be seen below,

```python
{
    "addresses": [
        {
            "addressID": "WastewaterSiteOttawa",
            "addL1": "123 Laurier Avenue",
            "addL2": "",
            "city": "Ottawa",
            "country": "Canada",
            "datasetID": "",
            "stateProvReg": "Ontario",
            "zipCode": "KE2 TYU"
        }
    ],
    "contacts": [
        {
            "contactID": "OttawaWWContact",
            "organizationID": "WWOttawa",
            "email": "ww@ottawa.ca",
            "phone": "6137458999",
            "firstName": "John",
            "lastName": "Doe",
            "role": "Technician",
            "notes": ""
        }
    ]
}
```

2. The validation rules argument is a dictionary that contains all the rules the data argument should be validated against. The argument is a cerberus schema whose details and shape can be seen [here](https://docs.python-cerberus.org/en/stable/schemas.html#). Finally, the ODM provides a [function](./convert-to-cerberus-schema.md) as well as a YAML object which contains the rules encoded in the latest version of the ODM dictionary.

## Return

The function should return a list of dictionaries, containing information about each error encountered during the validation process. The shape of the dictionary is dependant on the type of error and are outlined in the "Features" section below.

# Features

The next few sub sections specify what validation rules the function can currently handle. For each rule violation, the function will return an error report to help the user fix or debug the error.

## MissingMandatoryColumn

### Description

This rule is used to validate that all rows have the mandatory columns for that table.

For example, assume the user wants to validate the data shown below,

```python
{
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
```

with the following validation rules argument generated using the conversion function,

```python
{
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
                    "required" True,
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
```

The function should return only one error for the second row in the `Address` table which is missing the mandatory `addressID` column.

### Error Report

The error report will have the following fields

* **errorType**: MissingMandatoryColumn
* **tableName**: The name of the table the error object is for
* **columnName** The name of the column the error object is for
* **rowNumber**: The row number with the error
* **row** The dictionary containing the errorred row
* **validationRules**: The ODM data dictionary rule fields violated by this row
* **message**: Missing mandatory column <columnName> in table <tableName> in row number <rowIndex>

For the above example the function would return the following error report,

```python
[
    {
        "errorType": "MissingMandatoryColumn",
        "tableName": "addresses",
        "columnName": "addressID",
        "rowNumber": 2,
        "row": {
            "addL2": "12345 Lane Avenue"
        },
        "validationRules": {
            "partID": "addressID",
            "AddressTableRequired": "mandatory"
        },
        "message": "Missing mandatory column addressID in table Address in row number 2"
    }
]
```
