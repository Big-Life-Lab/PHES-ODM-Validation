# duplicate_values_found

This rule checks if a unique column has any duplicate values. For example, the `addId` column in the addresses table is the primary key for that table and should only have unique values. The following dataset would not pass validation due to the first two rows having the same value of `1` in their `addId` column.

```python
[
    "addresses": [
        {
            "addId": "1"
        },
        {
            "addId": "1"
        },
        {
            "addId": "3"
        }
    ]
]
```

The following dataset would pass validation since all the `addId` columns are different,

```python
[
    "addresses": [
        {
            "addId": "1"
        },
        {
            "addId": "2"
        },
        {
            "addId": "3"
        }
    ]
]
```

Currently, only primary key columns will have this rule.

## Error report

The error report will have the following fields

* **errorType**: duplicate_values_found
* **tableName**: The name of the table whose unique column(s) has duplicate values
* **columnName** The name of the unique column with duplicate values
* **rowNumbers**: The indexes of the rows with same values
* **rows** The rows in the data that failed this validation rule
* **invalidValue**: The duplicate value
* **validationRuleFields**: The ODM data dictionary rule fields violated by this row
* **message**: Duplicate values found in rows <row_indexes> for unique column <column_name> in table <table_name>

An example error report for the invalid dataset shown above,

```python
[
    {
        "errorType": "duplicate_values_found",
        "tableName": "addresses",
        "columnName": "addId",
        "rowNumbers": [1,2],
        "rows": [
            {
                "addId": "1"
            },
            {
                "addId": "1"
            }
        ],
        "invalidValue": "1",
        "validationRuleFields": [
            {
                "partID": "addId",
                "addresses": "pK"
            }
        ],
        "message": "Duplicate values found in rows 1 and 2 for unique column addId in table addresses"
    }
]
```

In addition, a seperate error report object should be generated for each set of duplicate values found. For example for the following dataset,

```python
[
    "addresses": [
        {
            "addId": "1"
        },
        {
            "addId": "1"
        },
        {
            "addId": "1"
        },
        {
            "addId": "3"
        },
        {
            "addId": "2"
        },
        {
            "addId": "2"
        }
    ]
]
```

two error report objects should be generated, one for the duplicate value `1` and one for the duplicate value `2`.

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. Currently, this rule is only applies to the [primary column for a table](../specs/odm-how-tos.md#how-to-get-the-columns-names-for-a-table).

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

Cerberus currently does not have support for unique column values. We will need to [extend the cerberus validator](https://docs.python-cerberus.org/en/stable/customize.html) to accomplish this.

The generated cerberus object for the example above is shown below,

```python
{
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addId": {
                    "unique": True,
                    "meta": [
                        {
                            "ruleId": "duplicate_values_found",
                            "meta": [
                                {
                                    "partID": "addId",
                                    "addresses": "pK",
                                    "version1Table": 
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

## Version 1

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
                    "unique": True,
                    "meta": [
                        {
                            "ruleId": "duplicate_values_found",
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