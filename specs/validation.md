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