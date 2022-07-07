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