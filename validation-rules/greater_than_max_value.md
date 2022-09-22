# greater_than_max_value

This rule ensure that columns values are not greater than a defined maximum value. Currently, this rule only supports columns whose data type is float or integer i.e. numbers. As an example, consider the `geoLat` column in the `sites` table which has a maximum value of 90. The following dataset snippet would fail validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": 91
        }
    ]
}
```

whereas the following dataset snippet would pass validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": 89
        }
    ]
}
```

The ODM dictionary is currently written so that the defined maximum values are inclusive i.e. only values greater than the maximum values are invalid. All other values should pass this rule. For example, for the `geoLat` column, a value of 90 would be valid.

## Error report

The error report will have the following fields

* **errorType**: greater_than_max_value
* **tableName** The name of the table with the invalid value
* **columnName**: The name of the column with the invalid value
* **rowNumber**: The index of the row with the invalid value
* **row**: The dictionary containing the invalid row
* **validationRuleFields**: The ODM data dictionary rows used to generate this rule
* **message**: Value <invalid_value> in row <row_index> in column <column_name> in table <table_name> is greater than the allowable maximum value of <max_value>

The error report object for the example invalid row above,

```python
[
    {
        "errorType": "greater_than_max_value",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": 91
        },
        "validationRules": {
            "partID": "geoLat",
            "min": "90"
        },
        "message": "Value 91 in row 1 in column geoLat in table sites is greater than the allowable maximum value of 90"
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. The steps involved are:

1. [Get the table names in the dictionary](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
1. [Get all the columns for each table](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
2. Filter the rows to include only those columns whose data type is float or integer
    * The `dataType` column in the parts sheet contains this metadata
    * It has a number of possible values but we're looking for values of `float` or `integer`
3. Check whether the filtered rows has a maximum value. If it does then add the validation rule for that column.
    * The `maxValue` column contains this metadata
    * The possible values are a number or `NA`. 
        * If the value is `NA` then this column does not have a maximum value.

For example in the following ODM dictionary snippet,

```python
[
    {
        "partID": "geoLat",
        "sites": "header",
        "dataType": "float",
        "max": "90"
    },
    {
        "partID": "geoEPSG",
        "sites": "header",
        "dataType": "float",
        "max": "NA"
    }
]
```

The `geoLat` part which is a column in the `sites` table has a `max` value of 90 and would have this rule set for it. On the other hand, the `geoEPSG` part which is also a column in the `sites` table would not have this rule due its `max` value being `NA`.

## Cerberus Schema

Although the cerberus library supports [maximum value validation](https://docs.python-cerberus.org/en/stable/validation-rules.html#min-max), it does not support the greater than **or** equal to operation. We will need to [extend the cerberus validator](https://docs.python-cerberus.org/en/stable/customize.html) to support this with a new `maxExclusive` rule.

The generated cerberus object for the example above is shown below,

```python
{
    "sites": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "geoLat": {
                    "maxInclusive": True,
                    "meta": [
                        {
                            "ruleId": "greater_than_max_value",
                            "meta": [
                                {
                                    "partID": "geoLat",
                                    "max": "90"
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

The metadata for this rule should include the row from the ODM for the part with its `partID` and `max` column values.

## ODM Version 1

When generating the schema for version 1, we check whether the column has an [equivalent part in version 1](../specs/odm-how-tos.md#getting-the-version-1-equivalent-for-a-part). If it does, then we add it to the cerberus schema. For example,

```python
[
    {
        "partID": "geoLat",
        "sites": "header",
        "version1Location": "variables",
        "version1Table": "Site",
        "version1Variable": "geoLat"
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
                "geoLat": {
                    "maxInclusive": True,
                    "meta": [
                        {
                            "ruleId": "greater_than_max_value",
                            "meta": [
                                {
                                    "partID": "geoLat",
                                    "sites": "header",
                                    "version1Location": "variables",
                                    "version1Table": "Site",
                                    "version1Variable": "geoLat",
                                    "max": "90"
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
* The `version1Location` column value
* The `version1Table` column value
* The `version1Variable` column value
* The `max` column value