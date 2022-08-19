# MissingMandatoryColumn

This rule checks if the rows of each table contains its mandatory columns. For example, the `addressID` column is mandatory for the `addresses` table. The following address table row,

```python
{
    "addL2": "123 Doe Street"
}
```

would fail validation. The following address table row would pass validation,

```python
{
    "addressID": "1"
    "addL2": "123 Doe Street"
}
```

## Error report

The error report will have the following fields

* **errorType**: MissingMandatoryColumn
* **tableName**: The name of the table containing the missing column
* **columnName** The name of the missing column
* **rowNumber**: The index of the table row with the error
* **row** The dictionary containing the row
* **validationRuleFields**: The ODM data dictionary rule fields violated by this row
* **message**: Missing mandatory column <columnName> in table <tableName> in row number <rowIndex>

Example

```python
[
    {
        "errorType": "MissingMandatoryColumn",
        "tableName": "addresses",
        "columnName": "addressID",
        "rowNumber": 1,
        "row": {
            "addL2": "123 Doe Street"
        },
        "validationRules": {
            "partID": "addressID",
            "addressesRequired": "mandatory"
        },
        "message": "Missing mandatory column addressID in table addresses in row number 1"
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. The relevant columns are:

* **partID**: Contains the name of a part
* **<table_name>**: Used to indicate whether the part is associated with a table
    
    Can have one of the following values:
    * **PK**: The part is a primary key for the table
    * **FK**: The part is a foreign key for the table
    * **header**: The part is the name of a column in the table
    * **input**
    * **NA**: The part is not applicable to the table
* **<table_name>Required**: Used to indicate whether a column is mandatory for a table

    Can have one of the following values:
    * **mandatory**: The column is mandatory
    * **optional**: The column is not mandatory
    * **NA**: The column is not applicable

Example

```python
{
    "parts": [
        {
            "partID": "addresses",
            "partType": "table",
            "addresses": "NA",
            "addressesRequired": "NA",
            "contacts": "NA",
            "contactsRequired": "NA"
        },
        {
            "partID": "contacts",
            "partType": "table",
            "addresses": "NA",
            "addressesTable": "NA",
            "contacts": "NA",
            "contactsRequired": "NA"
        }
        {
            "partID": "addressID",
            "partType": "attribute",
            "addresses": "PK",
            "addressesRequired": "mandatory",
            "contacts": "NA",
            "contactsRequired": "NA"
        },
        {
            "partID": "addL2",
            "partType": "attribute",
            "addresses": "header",
            "addressesRequired": "optional",
            "contacts": "NA",
            "contactsRequired": "NA"
        },
        {
            "partID": "contactID",
            "partType": "attribute",
            "addresses": "NA",
            "addressesRequired": "NA",
            "contacts": "PK",
            "contactsRequired": "NA"
        }
    ]
}
```

## Cerberus Schema

The generated cerberus object for the example above is shown below,

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
                        "partID": "addL2",
                        "addresses": "PK",
                        "addressesRequired": "NA"
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
                        "contacts": "PK",
                        "contactsRequired": "mandatory"
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

The data dictionary columns that should be included in the `meta` field are:
* partID
* <table_name>
* <table_name>Required

## Version 1

We need three pieces of information to make the cerberus schema for version 1:

1. The columns that are part of the version 1 table
2. The version 2 equivalent for each column
2. The version 2 equivalent for the table

Details for the above points can be found [here](./README.md/#version-1)

We then check if the version 2 equivalent column is mandatory in the version 2 equivalent table, if it is, then it should be mandatory in version 1. For example,

```python
{
    "parts": [
        {
            "partID": "instruments",
            "partType": "table",
            "version1Table": "Instrument",
            "version1Location": "tables",
            "version1Variable": "",
            "instrumentsRequired": "NA"
        },
        {
            "partID": "model",
            "partType": "attribute",
            "version1Table": "Instrument",
            "version1Location": "variables",
            "version1Variable": "model",
            "instrumentsRequired": "Required"
        }
    ]
}
```

The `model` partID has a version 1 equivalent which is also named `model`. The version 1 column is present in the `Instrument` table in version 1. The version 2 column is mandatory in the `instruments` table, which is the version 2 equivalent for the `Instrument` table in version 1. Hence, the `model` column is also mandatory in version 1. 

The `meta` field for version 1 should include the parts row with the `Required` keyword. For example, the `meta` field for the example would be,

```python
{
    "partID": "model",
    "partType": "attribute",
    "version1Table": "Instrument",
    "version1Location": "variables",
    "version1Variable": "model",
    "instrumentsRequired": "Required"
}
```

