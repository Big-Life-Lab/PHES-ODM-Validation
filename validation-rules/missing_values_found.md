# missing_values_found

This rule checks if mandatory columns contain any missing values. The ODM dictionary contains parts to define what is considered a missing value using the part type value of `missingness`. 

An example snippet dataset that would fail this rule is shown below. Assume in the following examples that values of **na** are considered missing.

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "na"
        },
        {
            "siteID": "2",
            "geoLat": 1
        }
    ]
}
```

The above dataset snippet would fail validation since the `geoLat` column is mandatory in the `sites` table and has a missing value in the first row.

The following dataset snippet would pass validation

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": 2
        },
        {
            "siteID": "2",
            "geoLat": 1
        }
    ]
}
```

## Error report

The error report should have the following fields

* **errorType**: missing_values_found
* **tableName**: The name of the table containing the missing values
* **columnName**: The name of the mandatory column containing the missing values
* **rowNumber**: The index of the table row with the error
* **row**: The dictionary containing the row
* **validationRuleFields**: The ODM data dictionary rows used to generate this rule
* **message**: Mandatory column <column_name> in table <table_name> contains missing value <invalid_value> in row index <row_index>

The error report object for the example invalid row above,

```python
[
    {
        "errorType": "missing_values_found",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": "na"
        },
        "validationRuleFields": [
            {
                "partID": "na",
                "partType": "missingness"
            },
            {
                "partID": "geoLat",
                "sitesRequired": "mandatory"
            }
        ],
        "message": "Mandatory column geoLat in table sites contains missing value na in row index 1"
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. The steps involved are:

1. Get all values that represent missing from the parts sheet
    1. Filter the parts to only include those whose `partType` column is `missingness`
    2. [Filter the rows to only include those parts valid for the needed version of the ODM](../specs/module-functions.md#working-with-the-version-parameter)
    2. The `partID` column has the missing value
2. [Get all mandatory columns for each table](../specs/odm-how-tos.md#checking-if-a-column-is-mandatory-for-a-table)
3. Add this rule for each mandatory column

For example in the ODM snippet below,

```python
[
    {
        "partID": "na",
        "partType": "missingness",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "NA",
        "sitesRequired": "NA"
    },
    {
        "partID": "nan",
        "partType": "missingness",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "NA",
        "sitesRequired": "NA"
    },
    {
        "partID": "NA",
        "partType": "missingness",
        "firstReleased": "1.0",
        "lastUpdated": "2.0",
        "status": "depreciated",
        "sites": "NA",
        "sitesRequired": "NA"
    },
    {
        "partID": "geoLat",
        "partType": "attribute",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "mandatory"
    },
    {
        "partID": "geoLong",
        "partType": "attribute",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "optional"
    }
]
```

if we're generating the schema for version 2.0 datasets and above, the missing values would be **na** and **nan**. The **NA** missing value described in the third part is only valid for datasets below 2.0. The validation rule would only be applied to the `geoLat` column in the `sites` table and not the `geoLong` column.

## Cerberus Schema

Although the cerberus library has a `nullable` rule, it does not allow customization of the null values. Instead, we will use the forbidden rule. For the example above the generated cerberus schema would be,

```python
{
    "sites": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "geoLat": {
                    "forbidden": ["na", "nan"],
                    "meta": [
                        {
                            "ruleId": "missing_values_found",
                            "meta": [
                                    {
                                        "partID": "na",
                                        "partType": "missingness"
                                    },
                                    {
                                        "partID": "nan",
                                        "partType": "missingness"
                                    },
                                    {
                                        "partID": "geoLat",
                                        "sitesRequired": "mandatory"
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

The `meta` field for this rule should include:

1. The parts sheet rows for the missing values. These dictionaries should include the `partID` and `partType` columns
2. The parts sheet row for the mandatory column. This dictionary should include the `partID` and `<table_name>Required` columns

## ODM Version 1

For version 1 we use the same steps as above with the following caveats,

1. Get the missing values that are only valid for version 1
2. Apply the rule to only those version 2 mandatory columns that have a [version 1 equivalent](../specs/odm-how-tos.md#getting-the-version-1-equivalent-for-a-part)

For the ODM snippet below,

```python
[
    {
        "partID": "na",
        "partType": "missingness",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "NA",
        "sitesRequired": "NA",
        "version1Location": "NA",
        "version1Table": "NA",
        "version1Variable": "NA"
    },
    {
        "partID": "nan",
        "partType": "missingness",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "NA",
        "sitesRequired": "NA",
        "version1Location": "NA",
        "version1Table": "NA",
        "version1Variable": "NA"
    },
    {
        "partID": "NA",
        "partType": "missingness",
        "firstReleased": "1.0",
        "lastUpdated": "2.0",
        "status": "depreciated",
        "sites": "NA",
        "sitesRequired": "NA",
        "version1Location": "NA",
        "version1Table": "NA",
        "version1Variable": "NA"
    },
    {
        "partID": "geoLat",
        "partType": "attribute",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "mandatory",
        "version1Location": "variables",
        "version1Table": "Site",
        "version1Variable": "latitude"
    },
    {
        "partID": "geoLong",
        "partType": "attribute",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "optional",
        "version1Location": "variables",
        "version1Table": "Site",
        "version1Variable": "longitude"
    }
]
```

The corresponding cerberus schema would be,

```python
{
    "Site": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "latitude": {
                    "forbidden": ["NA"],
                    "meta": [
                        {
                            "ruleId": "missing_values_found",
                            "meta": [
                                    {
                                        "partID": "NA",
                                        "partType": "missingness"
                                    },
                                    {
                                        "partID": "geoLat",
                                        "sitesRequired": "mandatory",
                                        "version1Location": "variables",
                                        "version1Table": "Site",
                                        "version1Variable": "latitude"
                                    },
                                ]
                        }
                    ]
                }
            }
        }
    }
}
```

The meta field should include the same parts sheet rows as for version 2 along with the following additional columns for the column part,

* **version1Location**
* **version1Table**
* **version1Variable**