# less_than_min_length

This rule ensures that the number of characters in a string type column is not less than a defined minimum value. As an example, consider the `phone` column in the `contacts` table whose minimum length value is 10. The following dataset snippet would fail validation,

```python
{
    "contacts": [
        {
            "contactID": "1",
            "phone": "123-456-1"
        }
    ]
}
```

The `phone` column in the first row has only 9 characters which is less than the minimum length value of 10, whereas the following dataset snippet would pass validation,

```python
{
    "contacts": [
        {
            "contactID": "1",
            "phone": "123-456-23"
        },
        {
            "contactID": "2",
            "phone": "123-456-231"
        }
    ]
}
```

The `phone` columns in both rows have a number of characters equal to 10 and 11 respectively which is greater than or equal to the minimum length value of 10.

## Error report

The error report should have the following fields,

* **errorType**: less_than_min_length
* **tableName**: The name of the table with the invalid value
* **columnName**: The name of the column with the invalid value
* **rowNumber**: The index of the row with the invalid value
* **row**: The dictionary containing the invalid row
* **validationRuleFields**: The ODM data dictionary rows used to generate this rule
* **message**: Value <invalid_value> in row <row_index> in column <column_name> in table <table_name> has length <invalid_length> which is less than the min length of <min_length>

The error report object for the example invalid row above is shown below,

```python
[
    {
        "errorType": "less_than_min_length",
        "tableName": "contacts",
        "columnName": "phone",
        "rowNumber": 1,
        "row": {
            "contactID": "1",
            "phone": "123-456-1"
        },
        "validationRuleFields": [
            {
                "partID": "phone",
                "minLength": "10"
            }
        ],
        "message": "Value 123-456-1 in row 1 in column phone in table contacts has length 9 which is less than the min length of 10"
    }
]
```

## Rule metadata

All the metadata for this rule is contained in the parts sheet in the ODM dictionary. The steps involved are:

1. [Get the table names in the dictionary](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
2. [Get all the columns for each table](../specs/odm-how-tos.md#how-to-get-the-names-of-tables-that-are-part-of-the-odm)
3. Filter the rows to only include those whose [data type is a string](../specs/odm-how-tos.md#getting-the-data-type-for-a-column). Currently, these are `varchar` columns.
4. Check whether the rows has a minimum length value. If it does then add the validation rule for that column.
    * The `minLength` column contains this metadata
    * The possible values are a number or `NA`
        * If the value is `NA` then this column does not have a minimum length value

For example in the following ODM dictionary snippet,

```python
[
    {
        "partID": "phone",
        "addresses": "NA",
        "contacts": "header",
        "dataType": "varchar",
        "minLength": "10"
    },
    {
        "partID": "addL2",
        "addresses": "header",
        "contacts": "NA",
        "dataType": "varchar",
        "minLength": "NA"
    }
]
```

The `phone` in the `contacts` table would have this validation rule but the `addL2` column in the `addresses` table would not.

## Cerberus Schema

We can use the [minLength](https://docs.python-cerberus.org/en/stable/validation-rules.html#minlength-maxlength) validation rule in the cerberus library to implement this.

The generated cerberus object for the example above is shown below,

```python
{
    "contacts": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "phone": {
                    "minLength": 10,
                    "meta": [
                        {
                            "ruleId": "less_than_min_length",
                            "meta": [
                                {
                                    "partID": "phone",
                                    "minLength": "10"
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

The metadata for this rule should have the row from the ODM parts sheet for the column with its `partID` and `minLength` column values.

## ODM Version 1

When generating the schema for version 1, we check whether the column has an [equivalent part in version 1](../specs/odm-how-tos.md#getting-the-version-1-equivalent-for-a-part). If it does, then we add it to the cerberus schema. For example,

```python
[
    {
        "partID": "phone",
        "contacts": "header",
        "minLength": "10",
        "version1Location": "variables",
        "version1Table": "Contact",
        "version1Variable": "phoneNumber"
    }
]
```

The corresponding cerberus schema would be,

```python
{
    "Contact": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "phone": {
                    "minLength": 10,
                    "meta": [
                        {
                            "ruleId": "less_than_min_value",
                            "meta": [
                                {
                                    "partID": "phone",
                                    "contacts": "header",
                                    "minLength": "10",
                                    "version1Location": "variables",
                                    "version1Table": "Contact",
                                    "version1Variable": "phoneNumber"
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
* The `minLength` column value
* The `version1Location` column value
* The `version1Table` column value
* The `version1Variable` column value