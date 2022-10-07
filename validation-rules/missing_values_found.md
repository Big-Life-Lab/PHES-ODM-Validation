# missing_values_found

This rule checks if a mandatory column contain any missing values. A value is considered missing if it contains an empty string.

Consider a mandatory column named `geoLat` in a `sites` table. The following ODM dataset snippet would fail validation due to the first row having an empty string for the `geoLat` column value. 

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": ""
        },
        {
            "siteID": "2",
            "geoLat": "1"
        }
    ]
}
```

In addition, column values that are an empty string when trimmed should also fail this validation rule. For example, the following ODM data snippet would also fail validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "  "
        },
        {
            "siteID": "2",
            "geoLat": "1"
        }
    ]
}
```

The following dataset snippet would pass validation

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "2"
        },
        {
            "siteID": "2",
            "geoLat": "1"
        }
    ]
}
```

## Warning report

A value that is invalid due to this rule should generate a **warning** and **not** an error. The warning report should have the following fields

* **warningType**: missing_values_found
* **tableName**: The name of the table containing the missing values
* **columnName**: The name of the mandatory column containing the missing values
* **rowNumber**: The index of the table row with the error
* **row**: The dictionary containing the row
* **validationRuleFields**: The ODM data dictionary rows used to generate this rule
* **message**: Mandatory column <column_name> in table <table_name> has an empty value in row <row_index>. Was this intentional?

The warning report object for the example ODM datasets in the previous section are shown below.

Example 1 warning report,

```python
[
    {
        "warningType": "missing_values_found",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": ""
        },
        "validationRuleFields": [
            {
                "partID": "geoLat",
                "sitesRequired": "mandatory"
            }
        ],
        "message": "Mandatory column geoLat in table sites has an empty value in row 1. Was this intentional?"
    }
]
```

Example 2 warning report,

```python
[
    {
        "warningType": "missing_values_found",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": "  "
        },
        "validationRuleFields": [
            {
                "partID": "geoLat",
                "sitesRequired": "mandatory"
            }
        ],
        "message": "Mandatory column geoLat in table sites has an empty value in row 1. Was this intentional?"
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. The steps involved are:

1. [Get the table names from the dictionary](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
2. [Get all mandatory columns for each table](../specs/odm-how-tos.md#checking-if-a-column-is-mandatory-for-a-table)
3. Add this rule for each mandatory column

For example in the ODM snippet below,

```python
[
    {
        "partID": "sites",
        "partType": "table",
        "firstReleased": "1.0",
        "status": "active",
        "sites": "NA",
        "sitesRequired": "NA"
    },
    {
        "partID": "geoLat",
        "partType": "attribute",
        "firstReleased": "1.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "mandatory"
    },
    {
        "partID": "geoLong",
        "partType": "attribute",
        "firstReleased": "1.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "optional"
    }
]
```

we would add this rule only to the `geoLat` column in the `sites` table. This rule would **not** be added to the `geoLong` column in the same table.

## Cerberus Schema

Although the cerberus library has an `empty` rule, the rule allows values that are "empty" once trimmed. We will need to create a new cerberus rule called `trimEmpty` to implement this validation rule. The cerberus schema for the ODM snippet above is shown below,

```python
{
    "sites": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "geoLat": {
                    "trimEmpty": False,
                    "meta": [
                        {
                            "ruleId": "missing_values_found",
                            "meta": [
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

The `meta` field for this rule should have only one entry, the row from the parts sheet for the mandatory column. The entry should include the `partID` and the `<table_name>Required` fields.

## ODM Version 1

For version 1 validation schemas, we add this rule to only those version 2 columns which have a [version 1 equivalent part](../specs/odm-how-tos.md#getting-the-version-1-equivalent-for-a-part).

For the ODM snippet below,

```python
[
    {
        "partID": "sites",
        "partType": "table",
        "firstReleased": "1.0",
        "status": "active",
        "sites": "NA",
        "sitesRequired": "NA",
        "version1Location": "tables",
        "version1Table": "Site",
        "version1Variable": "NA"
    },
    {
        "partID": "geoLat",
        "partType": "attribute",
        "firstReleased": "1.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "mandatory",
        "version1Location": "variables",
        "version1Table": "Site",
        "version1Variable": "latitude"
    },
    {
        "partID": "siteName",
        "partType": "attribute",
        "firstReleased": "2.0",
        "status": "active",
        "sites": "header",
        "sitesRequired": "mandatory",
        "version1Location": "NA",
        "version1Table": "NA",
        "version1Variable": "NA"
    },
    {
        "partID": "geoLong",
        "partType": "attribute",
        "firstReleased": "1.0",
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
                    "trimEmpty": False,
                    "meta": [
                        {
                            "ruleId": "missing_values_found",
                            "meta": [
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

The meta field for version 1 for this rule should include the `version1Location`, `version1Table`, and `version1Variable` columns in addition to the columns for version 2.