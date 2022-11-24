# invalid_type

This rule checks that the type of a value matches with a defined type or can be coerced into the defined type. There are a number of types in the ODM that this validation rule will need to handle, we'll go over each of them in the following sections.

## integer

An integer is defined as a number without a decimal point. Imagine a column `geoLat` in the sites table which is defined to be an integer. The following ODM data snippet would fail validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": 1.23
        }
    ]
}
```

whereas the following would pass validation

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": 1
        }
    ]
}
```

Values that are not explicitly integers but can be coerced into integers should pass validation. For example, the following should pass validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "1"
        },
        {
            "siteID": "2",
            "geoLat": 1.00
        }
    ]
}
```

A floating point number can be coerced into an integer if the coercion does not result in a value change. In above example, coercing 1.00 to its integer value of 1 does not change its value.

The snippet below should fail validation since they cannot be coerced to integers.

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "a"
        },
        {
            "siteID": "2",
            "geoLat": 1.01
        }
    ]
}
```

## float

A float is a decimal number. Imagine the same `geoLat` column but its defined type is now a float. The following dataset snippet would fail validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "a"
        }
    ]
}
```

whereas the following would pass validation

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": 1.23
        }
    ]
}
```

Once again, values that can be coerced into floats should pass validation. All integers and certain strings can be coerced into floats. For example, the following snippet below should pass validation,

```python
{
    "sites": [
        {
            "siteID": "1",
            "geoLat": "1.0"
        },
        {
            "siteID": "2",
            "geoLat": 1
        }
    ]
}
```

## email

An email address. As an example, imagine a part with id `contactEmail` which is a header in a `labs` table and has its defined type to be `email`. The following ODM snippet would fail validation,

```python
{
    "labs": [
        {
            "labID": "1",
            "email": "john.doe"
        }
    ]
}
```

whereas the following should pass validation

```python
{
    "labs": [
        {
            "labID": "1",
            "email": "john.doe@email.com"
        }
    ]
}
```

## boolean

A column that can have one of two values, representing Yes/No. The category values representing Yes/No are encoded in the dictionary. For example, consider the `reportable` column in the `measures` table whose data type is boolean. Also, assume that `true` and `false` are the allowed boolean category values`. The following dataset snippet would fail validation,

```python
{
    "measures": [
        {
            "measureID": "1",
            "reportable": "Yes"
        }
    ]
}
```

whereas the following the would pass validation,

```python
{
    "measures": [
        {
            "measureID": "1",
            "reportable": "true"
        }
    ]
}
```

The category values are case-sensitive i.e. the boolean column value case should match the one in the category values. For example, the following would fail validation,

```python
{
    "measures": [
        {
            "measureID": "1",
            "reportable": "True"
        }
    ]
}
```

## categorical

This type is handled by the [invalid_category](./invalid_category.md) rule

## varchar

No validation is currently needed for this type since all the previously mentioned types can be coerced into a varchar.

## see measure

Can be ignored for now.

## Error report

The error report should have the following fields,

* **errorType**: invalid_type
* **tableName**: The name of the table with the invalid value
* **columnName**: The name of the column with the invalid value
* **rowNumber**: The index of the row with the invalid value
* **row**: The dictionary containing the invalid row
* **validationRuleFields**: The ODM data dictionary rows used to generate this rule
* **message**: Value <invalid_value> in row <row_index> in column <column_name> in table <table_name> has type <invalid_value_type> but should be of type <valid_type> or coercable into a <valid_type>.

For a boolean data type, the message is shown below,

* **message**: Row <row_index> in column <column_name> in table <table_name> is a boolean but has value <invalid_value>. Allowed values are <boolean_categories>.

The error report objects for the invalid examples above can be seen below,

integer

```python
[
    {
        "errorType": "invalid_type",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": 1.23
        },
        "validationRuleFields": [
            {
                "partID": "geoLat",
                "dataType": "integer",
                "sites": "header"
            }
        ],
        "message": "Value 1.23 in row 1 in column geoLat in table sites has type float but should be of type integer or coercable into a integer"
    }
]
```

integer

```python
[
    {
        "errorType": "invalid_type",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": "a"
        },
        "validationRuleFields": [
            {
                "partID": "geoLat",
                "dataType": "integer",
                "sites": "header"
            }
        ],
        "message": "Value a in row 1 in column geoLat in table sites has type varchar but should be of type integer or coercable into a integer"
    },
    {
        "errorType": "invalid_type",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "2",
            "geoLat": 1.01
        },
        "validationRuleFields": [
            {
                "partID": "geoLat",
                "dataType": "integer",
                "sites": "header"
            }
        ],
        "message": "Value 1.01 in row 2 in column geoLat in table sites has type varchar but should be of type integer or coercable into a integer"
    }
]
```

float

```python
[
    {
        "errorType": "invalid_type",
        "tableName": "sites",
        "columnName": "geoLat",
        "rowNumber": 1,
        "row": {
            "siteID": "1",
            "geoLat": "a"
        },
        "validationRuleFields": [
            {
                "partID": "geoLat",
                "dataType": "float",
                "sites": "header"
            }
        ],
        "message": "Value a in row 1 in column geoLat in table sites has type varchar but should be of type float or coercable into a float"
    }
]
```

email

```python
[
    {
        "errorType": "invalid_type",
        "tableName": "labs",
        "columnName": "contactEmail",
        "rowNumber": 1,
        "row": {
            "labID": "1",
            "contactEmail": "john.doe"
        },
        "validationRuleFields": [
            {
                "partID": "john.doe",
                "dataType": "email",
                "labs": "header"
            }
        ],
        "message": "Value a in row 1 in column contactEmail in table labs has type varchar but should be of type email or coercable into an email"
    }
]
```

boolean 1

```python
[
    {
        "errorType": "invalid_type",
        "tableName": "measures",
        "columnName": "reportable",
        "rowNumber": 1,
        "row": {
            "measureID": "1",
            "reportable": "Yes"
        },
        "validationRuleFields": [
            {
                "partID": "reportable",
                "dataType": "boolean",
                "measures": "header"
            },
            {
                "partID": "true",
                "catSetID": "booleanSet"
            },
            {
                "partID": "false",
                "catSetID": "booleanSet"
            },
        ],
        "message": "Row 1 in column reportable in table measures is a boolean but has value Yes. Allowed values are true/false"
    }
]
```

boolean 2

```python
[
    {
        "errorType": "invalid_type",
        "tableName": "measures",
        "columnName": "reportable",
        "rowNumber": 1,
        "row": {
            "measureID": "1",
            "reportable": "True"
        },
        "validationRuleFields": [
            {
                "partID": "reportable",
                "dataType": "boolean",
                "measures": "header"
            },
            {
                "partID": "true",
                "catSetID": "booleanSet"
            },
            {
                "partID": "false",
                "catSetID": "booleanSet"
            },
        ],
        "message": "Row 1 in column reportable in table measures is a boolean but has value True. Allowed values are true/false"
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the ODM dictionary. The steps to retreive the metadata are:

1. [Get the table names in the dictionary](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
2. [Get all the columns for each table](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
3. [Get the defined data type for each column](../specs/odm-how-tos.md#getting-the-data-type-for-a-column). If the data type is a boolean then retreive the category values by:
    1. Filtering out all rows except for the ones whose `catSetID` is `booleanSet`
    2. The `partID` columns in the filtered rows contains the category values
4. Add this validation rule if the data type is supported by this validation rule. Currently, only `blob` and `datetime` are not supported and we don't need to add a rule for the `varchar` column.

For example, the parts sheet snippets for the examples above can be seen below,

For an integer `geoLat` column in a sites table

```python
{
    "parts": [
        {
            "partID": "sites",
            "partType": "tables",
            "sites": "NA",
            "dataType": "NA"
        },
        {
            "partID": "geoLat",
            "partType": "attribute",
            "sites": "header",
            "dataType": "integer"
        }
    ]
}
```

For a float `geoLat` column in a sites table

```python
{
    "parts": [
        {
            "partID": "sites",
            "partType": "tables",
            "sites": "NA",
            "dataType": "NA"
        },
        {
            "partID": "geoLat",
            "partType": "attribute",
            "sites": "header",
            "dataType": "float"
        }
    ]
}
```

For the email `contactEmail` column in the labs table

```python
{
    "parts": [
        {
            "partID": "labs",
            "partType": "tables",
            "labs": "NA",
            "dataType": "NA"
        },
        {
            "partID": "contactEmail",
            "partType": "attribute",
            "labs": "header",
            "dataType": "email"
        }
    ]
}
```

For the boolean `reportable` column in the `measures` table,

```python
{
    "parts": [
        {
            "partID": "measures",
            "partType": "table",
            "measures": "NA",
            "dataType": "NA",
            "catSetID": "NA"
        },
        {
            "partID": "reportable",
            "partType": "attribute",
            "measures": "header",
            "dataType": "boolean",
            "catSetID": "NA"
        },
        {
            "partID": "true",
            "partType": "category",
            "measures": "NA",
            "dataType": "varchar",
            "catSetID": "booleanSet"
        },
        {
            "partID": "false",
            "partType": "category",
            "measures": "NA",
            "dataType": "varchar",
            "catSetID": "booleanSet"
        }
    ]
}
```

## Cerberus schema

We can use the [type](https://docs.python-cerberus.org/en/stable/validation-rules.html#type) rule in cerberus to perform this validation. Cerberus by default does not coerce the data before validating, we will need to explicitly tell it to do so by using the [coerce](https://docs.python-cerberus.org/en/stable/normalization-rules.html#value-coercion) field.

For an `email` type we will need to create a [custom type](https://docs.python-cerberus.org/en/stable/customize.html#new-types) in cerberus.

For a `boolean` type we will need to use the [allowed](https://docs.python-cerberus.org/en/stable/validation-rules.html#allowed) rule in cerberus.

The generated cerberus objects for the examples above are shown below,

integer

```python
{
    "sites": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "geoLat": {
                    "type": "integer",
                    "coerce": int
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "geoLat",
                                    "dataType": "integer",
                                    "sites": "header"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "sites",
            "partType": "table"
        }
    }
}
```

float

```python
{
    "sites": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "geoLat": {
                    "type": "float",
                    "coerce": float
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "geoLat",
                                    "dataType": "float",
                                    "sites": "header"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "sites",
            "partType": "table"
        }
    }
}
```

email

```python
{
    "labs": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "contactEmail": {
                    "type": "email"
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "contactEmail",
                                    "dataType": "email",
                                    "labs": "header"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "labs",
            "partType": "table"
        }
    }
}
```

boolean

```python
{
    "measures": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "reportable": {
                    "type": "varchar",
                    "allowed": ["true", "false"]
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "contactEmail",
                                    "dataType": "email",
                                    "labs": "header"
                                },
                                {
                                    "partID": "true",
                                    "catSetID": "booleanSet"
                                },
                                {
                                    "partID": "false",
                                    "catSetID": "booleanSet
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "measures",
            "partType": "table"
        }
    }
}
```

The meta for this rule should include the `partID`, `<table_name>`, and `dataType`.

For a boolean data type, it should also include the rows that contain the category values. The `partID` and `catSetID` from each row should be included in the category value rows.

## ODM Version 1

When generating the schema for version 1, we check whether the column has an [equivalent part in version 1](../specs/odm-how-tos.md#getting-the-version-1-equivalent-for-a-part). If it does, then we add this validaton rule to it. For example, the v1 parts snippets for each of examples above are shown below,

integer

```python
{
    "parts": [
        {
            "partID": "sites",
            "partType": "tables",
            "sites": "NA",
            "dataType": "NA",
            "version1Location": "tables",
            "version1Table": "Site",
            "version1Variable": "NA"
        },
        {
            "partID": "geoLat",
            "partType": "attribute",
            "sites": "header",
            "dataType": "integer",
            "version1Location": "variables",
            "version1Table": "Site",
            "version1Variable": "Latitude"
        }
    ]
}
```

float

```python
{
    "parts": [
        {
            "partID": "sites",
            "partType": "tables",
            "sites": "NA",
            "dataType": "NA",
            "version1Location": "tables",
            "version1Table": "Site",
            "version1Variable": "NA"
        },
        {
            "partID": "geoLat",
            "partType": "attribute",
            "sites": "header",
            "dataType": "float",
            "version1Location": "tables",
            "version1Table": "Site",
            "version1Variable": "Latitude"
        }
    ]
}
```

email

```python
{
    "parts": [
        {
            "partID": "labs",
            "partType": "tables",
            "labs": "NA",
            "dataType": "NA",
            "version1Location": "tables",
            "version1Table": "Lab",
            "version1Variable": "NA"
        },
        {
            "partID": "contactEmail",
            "partType": "attribute",
            "labs": "header",
            "dataType": "email",
            "version1Location": "variables",
            "version1Table": "Lab",
            "version1Variable": "email"
        }
    ]
}
```

boolean

```python
{
    "parts": [
        {
            "partID": "measures",
            "partType": "table",
            "measures": "NA",
            "dataType": "NA",
            "catSetID": "NA",
            "version1Location": "tables",
            "version1Table": "Measure",
            "version1Variable": "NA",
            "version1Category": "NA"
        },
        {
            "partID": "reportable",
            "partType": "attribute",
            "measures": "header",
            "dataType": "boolean",
            "catSetID": "NA",
            "version1Location": "variables",
            "version1Table": "Measure",
            "version1Variable": "reported",
            "version1Category": "NA"
        },
        {
            "partID": "true",
            "partType": "category",
            "measures": "NA",
            "dataType": "varchar",
            "catSetID": "booleanSet",
            "version1Location": "NA",
            "version1Table": "NA",
            "version1Variable": "NA",
            "version1Category": "TRUE"
        },
        {
            "partID": "false",
            "partType": "category",
            "measures": "NA",
            "dataType": "varchar",
            "catSetID": "booleanSet",
            "version1Location": "tables",
            "version1Table": "Site",
            "version1Variable": "NA",
            "version1Category": "FALSE"
        }
    ]
}
```

The corresponding v1 cerberus schemas are shown below,

integer

```python
{
    "Site": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "Latitude": {
                    "type": "integer",
                    "coerce": int
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "geoLat",
                                    "dataType": "integer",
                                    "sites": "header",
                                    "version1Location": "variables",
                                    "version1Table": "Site",
                                    "version1Variable": "Latitude"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "sites",
            "partType": "table",
            "version1Location": "tables",
            "version1Table": "Site"
        }
    }
}
```

float

```python
{
    "Site": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "Latitude": {
                    "type": "float",
                    "coerce": float
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "geoLat",
                                    "dataType": "float",
                                    "sites": "header",
                                    "version1Location": "variables",
                                    "version1Table": "Site",
                                    "version1Variable": "Latitude"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "sites",
            "partType": "table",
            "version1Location": "tables",
            "version1Table": "Site"
        }
    }
}
```

email

```python
{
    "Lab": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "email": {
                    "type": "email"
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "contactEmail",
                                    "dataType": "email",
                                    "labs": "header",
                                    "version1Location": "variables",
                                    "version1Table": "Lab",
                                    "version1Variable": "email"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "labs",
            "partType": "table",
            "version1Location": "tables",
            "version1Table": "Lab"
        }
    }
}
```

boolean

```python
{
    "Measure": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "reported": {
                    "type": "varchar",
                    "allowed": ["TRUE", "FALSE"]
                    "meta": [
                        {
                            "ruleId": "invalid_type",
                            "meta": [
                                {
                                    "partID": "reportable",
                                    "dataType": "boolean",
                                    "measures": "header",
                                    "version1Location": "variables",
                                    "version1Table": "Measure",
                                    "version1Variable": "reported"
                                },
                                {
                                    "partID": "true",
                                    "catSetID": "booleanSet",
                                    "version1Category": "TRUE"
                                },
                                {
                                    "partID": "false",
                                    "catSetID": "booleanSet,
                                    "version1Category": "FALSE"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "meta": {
            "partID": "measures",
            "partType": "table",
            "version1Location": "tables",
            "version1Table": "Measure"
        }
    }
}
```

The metadata should include the meta columns for version 2 as well as the `version1Location`, `version1Table`, and the `version1Variable` columns.

For a boolean data type, only the `version1Category` column should be added on for the boolean category values.