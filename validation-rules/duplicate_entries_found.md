# duplicate_entries_found

This rule identifies when there are two identical entries with the same primary key. The rational has been described [here](https://odm.discourse.group/t/duplicate-entries-and-lastedited-field/55). In brief, the ODM can provide a papertrail of updates made to an entry by allowing users to update entries by: 1. Not deleting the old entry 2. Adding a new row for the updated entry and 3. Updating the `lastUpdated` field for the updated entry.

For validation, this rule would be violated if two rows have the same primary key values but non-unique `lastUpdated` values. For example, the following ODM data snippet would fail validation.

```python
[
    "addresses": [
        {
            "addId": "1",
            "lastUpdated": ""
        },
        {
            "addId": "1",
            "lastUpdated": ""
        },
        {
            "addId": "3"
        }
    ]
]
```

There are two rows (rows 1 and 2) with the same primary key value of `1` but also the same `lastUpdated` value.

The following dataset would also fail validation,

```python
[
    "addresses": [
        {
            "addId": "1",
            "lastUpdated": ""
        },
        {
            "addId": "1",
            "lastUpdated": "01/01/2023"
        },
        {
            "addId": "1",
            "lastUpdated": "01/01/2023"
        },
        {
            "addId": "3"
        }
    ]
]
```

The following dataset would pass validation,

```python
[
    "addresses": [
        {
            "addId": "1",
            "lastUpdated": ""
        },
        {
            "addId": "1",
            "lastUpdated": "01/01/2023"
        },
        {
            "addId": "1",
            "lastUpdated": "01/02/2023"
        },
        {
            "addId": "3"
        }
    ]
]
```

## Error report

The error report will have the following fields

* **errorType**: duplicate_entries_found
* **tableName**: The name of the table with duplicate entries
* **columnName** The name of the primary key column
* **rowNumbers**: The indexes of the duplicate entries
* **rows** The entries in the table that failed this validation rule
* **validationRuleFields**: The ODM data dictionary rule fields violated by this row
* **message**: Duplicate entries found in rows <row_indexes> with primary key column <column_name> and primary key value <primary_key_value> in table <table_name>

An example error report for the first invalid dataset shown above,

```python
[
    {
        "errorType": "duplicate_entries_found",
        "tableName": "addresses",
        "columnName": "addId",
        "rowNumbers": [1,2],
        "rows": [
            {
                "addId": "1",
                "lastUpdated": ""
            },
            {
                "addId": "1",
                "lastUpdated": ""
            }
        ],
        "validationRuleFields": [
            {
                "partID": "addId",
                "addresses": "pK"
            }
        ],
        "message": "Duplicate entries found in rows 1,2 with primary key column addId and primary key value 1 in table addresses"
    }
]
```

In addition, a seperate error report object should be generated for each set of duplicate values found. For example for the following dataset,

```python
[
    "addresses": [
        {
            "addId": "1",
            "lastUpdated": ""
        },
        {
            "addId": "1",
            "lastUpdated": "01/02/2023"
        },
        {
            "addId": "1",
            "lastUpdated": "01/02/2023"
        },
        {
            "addId": "3"
        },
        {
            "addId": "2",
            "lastUpdated": ""
        },
        {
            "addId": "2",
            "lastUpdated": ""
        }
    ]
]
```

Two error report objects should be generated, one for rows 2 and 3 and one for rows 5 and 6.

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. This rule should be added to the primary key column for all tables which can identified using these [instructions](../specs/odm-how-tos.md#how-to-get-the-columns-names-for-a-table).

For example,

```python
{
    "parts": [
        {
            "partID": "addId",
            "addresses": "pK"
        }
    ]
}
```

Here the `addId` part can be identified as being the primary key for the addresses table and hence should have this rule implemented.

## Cerberus Schema

Cerberus currently does not have support for this rule. We will need to [extend the cerberus validator](https://docs.python-cerberus.org/en/stable/customize.html) to accomplish this.

The generated cerberus object for the example above is shown below,

```python
{
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addId": {
                    "noDuplicateEntries": True,
                    "meta": [
                        {
                            "ruleId": "duplicate_entries_found",
                            "meta": [
                                {
                                    "partID": "addId",
                                    "addresses": "pK"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
}
```

The metadata for this rule should include the row from the ODM that defines this part as a primary key.

## ODM Version 1

When generating the schema for version 1, we check whether the primary key column has a version 1 equivalent column. If it does, then we add to the cerberus schema. For example,

```python
[
    {
        "partID": "addId",
        "addresses": "pk",
        "version1Location": "variables",
        "version1Table": "Address",
        "version1Variable": "AddressId"
    }
]
```

The corresponding cerberus schema would be,

```python
{
    "Address": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "AddressId": {
                    "noDuplicateEntries": True,
                    "meta": [
                        {
                            "ruleId": "duplicate_entries_found",
                            "meta": [
                                {
                                    "partID": "addId",
                                    "addresses": "pk",
                                    "version1Location": "variables",
                                    "version1Table": "Address",
                                    "version1Variable": "AddressId"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
}
```

The metadata should include the following columns,

* The `partID` column value
* The <table_name> column value 
* The `version1Location` column value
* The `version1Table` column value
* The `version1Variable` column value