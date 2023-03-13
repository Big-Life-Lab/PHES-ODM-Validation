# ODM How-to's

This file specifies methods for navigating the ODM data dictionary that can be referenced by different specification files in this repo.

## How to get the names of tables that are part of the ODM

We can use the `part` and `partType` columns for this. Any part ID whose `partType` is `tables` is considered to be a table. For example in the following dictionary,

```python
[
    {
        "part": "addresses",
        "partType": "tables"
    },
    {
        "part": "measures",
        "partType": "tables"
    },
    {
        "part": "addId",
        "partType": "attributes"
    }
]
```

`addresses` and `measures` are table names.

## How to get the columns names for a table

Once we have the [table names part of the dictionary](#how-to-get-the-columns-names-for-a-table), the dictionary has columns that match with these table names giving information on whether a part is a column for it. For example in the dictionary snippet below,

```python
[
    {
        "part": "addresses",
        "partType": "tables",
        "addresses: "NA",
        "contacts": "NA"
    },
    {
        "part": "addId",
        "partType": "attributes",
        "addresses: "pK",
        "contacts": "NA"
    },
    {
        "part": "addL1",
        "partType": "attributes",
        "addresses: "addL1",
        "contacts": "NA"
    },
    {
        "part": "contacts",
        "partType": "tables",
        "addresses: "addL1",
        "contacts": "NA"
    },
    {
        "part": "contID",
        "partType": "attributes",
        "addresses: "NA",
        "contacts: "pK"
    },
]
```

The tables are `addresses` and `contacts` and the `addresses` and `contacts` columns give information on which parts are their columns. Here, `addId` and `addL1` are columns in the addresses table and `contID` is a column in the contacts table. A part is a column in a table if it does not have a value of `NA` or `input` in the table column. In addition, the table column has additional possible values to describe the role a column plays in the table. All the possible values are,

* **pK**: The column is the primary key for the table
* **fK** The column is the foreign referencing a row in another table
* **header**: No special role
* **input**:
* **NA**: The part is a not a column in the table

## Getting the version 1 equivalent for a part

The parts sheet in the ODM dictionary has columns that indicate whether a part has a ODM version 1 equivalent. These columns can indicate whether a part was a table, column, or category in version 1 or if it does not have an equivalent in version 1. The column names and their metadata are shown below,

* **version1Location**: Whether this part was a table, column, or category in version 1 or NA if it does not have a version 1 equivalent. The possible values are:
    * **tables**: This part was a table in version 1
    * **variables**: This part was a column in version 1
    * **variableCategories**: This was was a variable category in version 1
* **version1Table**: The name of the version 1 table or NA. If `version1Location` is tables then this contains the version 1 table name for this part otherwise its the name of the table that the version 1 column or variable category belongs to.
* **version1Variable**: The name of the version 1 column or NA. If `version1Location` is variables then this contains the version 1 column name for this part otherwise its the name of the column that the version 1 variable category belongs to.
* **version1Category**: The name of the version 1 category or NA.

A part can have multiple version 1 equivalents each of which are seperated by a semi-colon (;) for example `Site;WWMeasure`.

Examples are given below.

The **instruments** part in version 2 is a table in version 1 called **Instrument**

```python
[
    {
        "part": "instruments",
        "version1Location": "tables",
        "version1Table": "Instrument",
        "version1Variable": "NA",
        "version1Category": "NA"
    }
]
```

The **measRepID** part in version 2 is a column in version 1 called **uWwMeasureID** in the **WWMeasure** version 1 table

```python
[
    {
        "part": "measRepID",
        "version1Location": "variables",
        "version1Table": "WWMeasure",
        "version1Variable": "uWwMeasureID",
        "version1Category": "NA"
    }
]
```

The **refLink** part in version 2 is a column in version 1 called **referenceLink** in the **AssayMethod** and **Instrument** version 1 tables

```python
[
    {
        "part": "refLink",
        "version1Location": "variables",
        "version1Table": "AssayMethod;Instrument",
        "version1Variable": "refLink",
        "version1Category": "NA"
    }
]
```

Finally, the **airTemp** part in version 2 is a category in version 1 called **envTemp** in the **SiteMeasure** version 1 table for the **type** column.

```python
[
    {
        "part": "airTemp",
        "version1Location": "variableCategories",
        "version1Table": "SiteMeasure",
        "version1Variable": "type",
        "version1Category": "envTemp"
    }
]
```

## Checking if a column is mandatory for a table

This can be done by looking at the `\<table_name\>Required` columns in the parts sheet. [The table names will need to be retreived](#how-to-get-the-names-of-tables-that-are-part-of-the-odm) first to identify these columns. The possible values for the `\<table_name\>Required` columns are:

* **mandatory**: This column is mandatory
* **optional**: This column is optional
* **NA**: This column is not valid for this table

For example in the ODM snippet below,

```python
[
    {
        "part": "geoLat",
        "sites": "header",
        "sitesRequired": "mandatory"
    },
    {
        "part": "geoLong",
        "sites": "header",
        "sitesRequired": "optional"
    },
    {
        "part": "measureID",
        "sites": "NA",
        "sitesRequired": "NA"
    }
]
```

The `geoLat` and `geoLong` columns in the sites table are mandatory and optional required while the `measureID` column is not present in the sites table.

## Getting the data type for a column

Once we have the [columns for a table](#how-to-get-the-columns-names-for-a-table), we can get its data type by using the `dataType` column in the parts sheet. The column has one of the following values:

* **varchar**
* **integer**
* **float**
* **boolean**
* **categorical**
* **blob**
* **datetime**
* **email**
* **see measure**: The data type for this part depends on the measure
