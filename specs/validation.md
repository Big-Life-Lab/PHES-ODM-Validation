# Function Signature

## Arguments

The function should accept two arguments, the ODM data to be validated and the ODM data dictionary which contains the validation rules.

1. The ODM data to be validated is a [dictionary](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) whose keys are the table names and values are the table rows represented as a [list](https://developers.google.com/edu/python/lists) of dictionaries. For each dictionary within the list, the keys are the column names and values are the column values. For example, the data argument for a dataset consisting of the Address and Contact table can be seen below,
    ```{python}
    {
        "Address": [
            {
                "addressID": "WastewaterSiteOttawa",
                "addL1": "123 Laurier Avenue",
                "addL2": "",
                "city": "Ottawa",
                "country": "Canada"
                "datasetID": "",
                "stateProvReg": "Ontario",
                "zipCode": "KE2 TYU"
            }
        ],
        "Contact": [
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

2. The metadata for the validation rules are defined in the [data dictionary](https://github.com/Big-Life-Lab/PHES-ODM/tree/V2-first-draft/template) and should be passed in as a dictionary. The **parts** and **sets** sheets contains the metadata needed and should be passed in as a list of dictionaries. An example can be seen below,

    ```{python}
    {
        "parts: [
            {
                "partID": "methodSetID",
                "label": Method Set ID",
                "partType": "attribute"
                "dataType": "varchar"
            }
        ],
        "sets": [
            {
                "setName (partID): "ynmCats",
                "setType": "category",
                "setValues (partID): "yes1"
            }
        ]
    }
    ```

    Keep in mind, that in the example above, all the columns in the sheets have not been included.

## Return

The function should return a list of dictionaries, containing information about each error encountered during the validation process. The shape of the dictionary is dependant on the type of error and are outlined in the "Features" section below.

# Features

## Validate the column names in a table

This rule is used to validate that the rows in a table has all its mandatory columns. For each table in the `data` argument, the metadata for this rule is present in the `parts` sheet in the `partID`, `<table_name>Table`, and `<table_name>Required` column.

The `partID` has the name of the column.

The `<table_name>Table` column encodes how the `partID` is included in the table. The possible values are:
1. **header**: Is a column in the table
2. **input**:
3. **PK**: Is a primary key column in the table
4. **FK**: Is a foreign key column in the table referencing another table
5. **NA**: Is not related to the table

The `<table_name>Required` column encodes whether a column is mandatory or not. The possible values are:
1. **mandatory**: The column is mandatory
2. **optional**: The column is optional
3. **NA**: The column is not part of the table

For example, assume the following validation rules metadata argument

```{python}
{
    "parts": [
        {
            "partID": "addressID",
            "AddressTable": "PK",
            "AddressTableRequired": "mandatory",
            "ContactTable": "NA",
            "ContactTableRequired": "NA"
        },
        {
            "partID": "addL2",
            "AddressTable": "header",
            "AddressTableRequired": "optional",
            "ContactTable": "NA",
            "ContactTableRequired": "NA"
        }
        {
            "partID": "contactID",
            "AddressTable": "NA",
            "AddressTableRequired": "NA",
            "ContactTable": "PK",
            "ContactTableRequired": "mandatory"
        }
    ]
}
```
and the user wants to validate the data below,

```{python}
{
    "Address": [
        {
            "addressID": "1",
        },
        {
            "addL2": "12345 Lane Avenue"
        }
    ],
    "Contact": [
        {
            "contactID": "1"
        }
    ]
}
```

The function should return only one error for the second row in the `Address` table which is missing the mandatory `addressID` column.

The returned error dictionary should have the following fields,

* **errorType**: MissingRequiredColumn
* **tableName**: The name of the table the error object is for
* **columnName** The name of the column the error object is for
* **rowIndex**: The index of the error row in the table
* **row** The dictionary containing the errorred row
* **validationRules**: The dictionary containing the metadata fields used to produce the error

For example, for the above example the function would return the following list,

```{python}
[
    {
        "errorType": "MissingRequiredColumn",
        "tableName": "Address",
        "columnName": "addressID",
        "rowIndex": 2,
        "row": {
            "addL2": "12345 Lane Avenue"
        },
        "validationRules": {
            "partID": "addressID",
            "AddressTable": "PK",
            "AddressTableRequired": "mandatory"
        }
    }
]
```