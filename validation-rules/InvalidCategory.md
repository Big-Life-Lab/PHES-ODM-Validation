# InvalidCategory

This rule checks if the rows of a categorical column in a table have the right values. A right value is one in the set of allowable values for the categorical column. For example, the `collection` column in the `samples` table is a categorical column whose set of allowable values or categories are `comp3h`, `comp8h`, `flowPr` etc. The following samples table row would fail validation,

```
{
    "collection": "flow"
}
```

The following samples table row would pass validation,

```
{
    "collection": "flowPr"
}
```

## Error report

The error report will have the following fields

* **errorType**: InvalidCategory
* **tableName**: The name of the table whose row has the invalid category
* **columnName** The name of the column with the invalid category
* **rowNumber**: The index of the table row with the error
* **row** The row in the data that failed this validation rule
* **invalidCategoryValue**: The invalid category value
* **validationRuleFields**: The ODM data dictionary rule fields violated by this row
* **message**: Invalid category <invalidCategoryValue> found in row <rowIndex> for column <columnName> in table <tableName>

Example

```python
[
    {
        "errorType": "InvalidCategory",
        "tableName": "samples",
        "columnName": "collection",
        "rowNumber": 1,
        "row": {
            "collection": "flow"
        },
        "invalidCategoryValue": "flow",
        "validationRuleFields": [
            {
                "partID": "samples",
                "partType": "table",
                "samples": "header",
                "dataType": "categorical",
                "catSetID": "collectCat"
            },
            {
                "partID": "comp3h",
                "partType": "category",
                "samples": "input",
                "dataType": "varchar",
                "catSetID": "collectCat"
            },
            {
                "partID": "comp8h",
                "partType": "category",
                "samples": "input",
                "dataType": "varchar",
                "catSetID": "collectCat"
            },
            {
                "partID": "flowPr",
                "partType": "category",
                "samples": "input",
                "dataType": "varchar",
                "catSetID": "collectCat"
            }
        ],
        "message": "Invalid category flow found in row 1 for column collection in table samples
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the data dictionary. The metadata is used to identify the following two pieces:

1. The categorical columns in a table. These are identified using the `partID`, `dataType`, and `<table_name>` columns. 
    * **partID**: Contains the name of a possible column
    * **<table_name>**: Whether the part is associated with a table. Look for values of **PK**, **FK**, or **header** to indicate that the part is the name of a column in the table.
    * **dataType**: A value of `categorical` is used to indicate that the part is categorical
2. The category values for a categorical column. These are identified using the `partID`, `partType`, and `catSetId` column.
    * **partID**: Contains the name of a possible category
    * **partType**: A value of `category` is used to indicate that the part is a category value
    * **catSetId**: The name of the category set that this category is for. The value will match up with the value in a categorical column.

Example

```python
{
    "parts": [
        {
            "partID": "collection",
            "partType": "attribute",
            "samples": "header",
            "dataType": "categorical",
            "catSetID": "collectCat"
        },
        {
            "partID": "comp3h",
            "partType": "category",
            "samples": "input",
            "dataType": "varchar",
            "catSetID": "collectCat"
        },
        {
            "partID": "comp8h",
            "partType": "category",
            "samples": "input",
            "dataType": "varchar",
            "catSetID": "collectCat"
        },
        {
            "partID": "flowPr",
            "partType": "category",
            "samples": "input",
            "dataType": "varchar",
            "catSetID": "collectCat"
        }
    ]
}
```

Here, the name of the categorical column is `collection` and its the name of a column in the `samples` table. The category set name is `collectCat` which is used to identify the category values which are `comp3h`, `comp8h`, and `flowPr`.

## Cerberus Schema

The generated cerberus object for the example above is shown below,

```python
{
    "samples": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "collection": {
                    "type": "string",
                    "allowed": ["comp3h", "comp8h", "flowPr"],
                    "meta": [
                        {
                            "ruleId": "InvalidCategory",
                            "meta": [
                                {
                                    "partID": "samples",
                                    "partType": "table",
                                    "samples": "header",
                                    "dataType": "categorical",
                                    "catSetID": "collectCat"
                                },
                                {
                                    "partID": "comp3h",
                                    "partType": "category",
                                    "samples": "input",
                                    "dataType": "varchar",
                                    "catSetID": "collectCat"
                                },
                                {
                                    "partID": "comp8h",
                                    "partType": "category",
                                    "samples": "input",
                                    "dataType": "varchar",
                                    "catSetID": "collectCat"
                                },
                                {
                                    "partID": "flowPr",
                                    "partType": "category",
                                    "samples": "input",
                                    "dataType": "varchar",
                                    "catSetID": "collectCat"
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

The metadata for this rule should include the following rows from the ODM dictionary:

* The part definition for the column in the table
* The part definition for each category that forms the category set for the categorical column