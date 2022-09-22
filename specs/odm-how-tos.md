This file specifies methods for navigating the ODM data dictionary that can be referenced by different specification files in this repo.

# How to get the names of tables that are part of the ODM

We can use the `partID` and `partType` columns for this. Any part ID whose `partType` is table is considered to be a table. For example in the following dictionary,

```python
[
    {
        "partID": "addresses",
        "partType": "table"
    },
    {
        "partID": "measures",
        "partType": "table"
    },
    {
        "partID": "addId",
        "partType": "attribute"
    }
]
```

`addresses` and `measures` are table names.

# How to get the columns names for a table

Once we have the [table names part of the dictionary](#how-to-get-the-columns-names-for-a-table), the dictionary has columns that match with these table names giving information on whether a part is a column for it. For example in the dictionary snippet below,

```python
[
    {
        "partID": "addresses",
        "partType": "table",
        "addresses: "NA",
        "contacts": "NA"
    },
    {
        "partID": "addId",
        "partType": "attribute",
        "addresses: "pK",
        "contacts": "NA"
    },
    {
        "partID": "addId",
        "partType": "attribute",
        "addresses: "addL1",
        "contacts": "NA"
    },
    {
        "partID": "contacts",
        "partType": "table",
        "addresses: "addL1",
        "contacts": "NA"
    },
    {
        "partID": "contID",
        "partType": "attribute",
        "addresses: "NA",
        "contacts: "pK"
    },
]
```

The tables are `addresses` and `contacts` and the `addresses` and `contacts` give information on which parts are their columns. Here, `addId` and `addL1` are columns in the addresses table and `contID` is a column in the contacts table. A part is a column in a table if it does not have a value of `NA` in the table column. In addition, the table column has additional possible values to describe hat role a column plays in the table. The possible values are:

* **pK**: The column is the primary key for the table
* **fK** The column is the foreign referencing a row in another table
* **header**: No special role
* **input**:
* **NA**: The part is a not a column in the table