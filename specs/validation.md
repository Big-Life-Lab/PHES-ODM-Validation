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

* Make sure each table for example `MeasureReport` has the correct column names
* Questions
    * Are there mandatory columns that each table should have?
* Metadata
    * Use the `parts` excel sheet
    * There's a column for each table for example `MeasureReport` which gives the metadata for that table
    * The `tableCat` value in the catSetID column outlines the categories
        * The pertinant values for this feature are:
            * header - Part that can be a column in the table
            * PK - Part that is the primary key column for the table
            * FK - Part that is the foreign key for another table
            * naTable - Part that does not apply to the table
    * The PK part is mandatory

## Validate the data type of each column in a table

* Make sure the values in each column are the right type. For example, a string has not been put into a column that should only have numbers
* Questions
    * Is there a document which explains what each of these data types are?
    * How do you get the valid categories for a category data type?
    * I don't think the "See unit" and "table" data types are valid for this?
* Info
    * The current allowed dataTypes are
        * any
        * blob
        * boolean
        * category
        * datetime
        * float
        * freetext
        * integer
        * NA
        * See unit
            * Look at value of the `unitSetID` column for this part. For example for `a1306s` its `geneticUnits`
            * Go to the sets sheet and find all the rows whose `setName` is equal to the `unitSetID` value
            * The allowed values are the filtered values for the `setValues` column. For example, for `geneticUnits` this is gcMl, ct, det, gcPpmov, gcGS, gcCrA, pp, gcL, prop, boc, doc,propV
        * table
        * varchar