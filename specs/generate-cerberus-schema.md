# Context

One of the arguments of the `validate_data` function is a [cerberus](https://docs.python-cerberus.org/en/stable/) object containing the validation rules to apply to the data. This function will convert the metadata encoded in the ODM data dictionary into a cerberus object that can be used by the `validate_data` function.

# Function Signature

## Arguments

The function will take one argument, a dictionary containing the parts sheet from the ODM data dictionary. The sheet can be view [here](https://github.com/Big-Life-Lab/PHES-ODM/tree/V2-first-draft/template). An example is shown below,

```python
{
    "parts": [
        {
            "partID": "addresses",
            "label": "Address table",
            "partType": "table",
            "addresses": "NA",
            "addressesRequired": "NA"
        },
        {
            "partID": "addressID",
            "label": "Address ID",
            "partType": "attribute",
            "addresses": "pK",
            "addressesRequired": "mandatory"
        }
    ]
}
```

## Return

The function will return a dictionary that is a valid cerberus validation object. In addition, values from the ODM data dictionary will also be added to the `meta` field for debugging purposes. For example, the above dictionary example should generate the following cerberus object,

```python
{
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
                    "required": True,
                    "meta": {
                        "partID": "addressID",
                        "addresses": "pK",
                        "addressesRequired": "mandatory"
                    }
                }
            }
        },
        "meta": {
            "partID": "addresses"
        }
    }
}
```

# Features

This section will go over the validation features in the [specification for the `validate_data` function](./validate-data.md), and specify the creation of the cerberus object for it. The final result of the function is a cerberus object that is a combination of all the objects specified in each sub-section below.

At a high level, the cerberus object is a dictionary whose field names are the names of the tables as specified in the ODM and whose field values contains the schema for that table, specified in the cerberus format. The list of table names can be retreived by looking at the `partID` and the `partType` column in the dictionary. A `partType` value of `table` implies that the corresponding part in the `partID` column is the name of a table. For example, consider the following ODM dictionary,

```python
{
    "parts": [
        {
            "partID": "addresses",
            "partType": "table"
        },
        {
            "partID": "contacts",
            "partType": "table"
        }
    ]
}
```

The corresponding cerberus high level object would be,

```python
{
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            # Fill in the remaining schema fields using the rest of the dictionary
        },
        "meta": {
            "partID": "addresses",
            "partType": "table"
        }
    },
    "contacts": {
        "type": "list",
        "schema": {
            "type": "dict",
            # Fill in the remaining schema fields using the rest of the dictionary
        },
        "meta": {
            "partID": "contacts",
            "partType": "table"
        }
    }
}
```

The cerberus schema for each object is a list of dictionaries since that's how we expect the user to pass in their data in the validation function. The remaining headers in this section add on to this base object using the other fields in the dictionary.

## MissingMandatoryColumn

The ODM dictionary fields used to generate the cerberus object for this rule are:

* **partID**: Contains the name of a part
* **<table_name>**: Used to indicate whether the part is associated with a table
    
    Can have one of the following values:
    * **PK**: The part is a primary key for the table
    * **FK**: The part is a foreign key for the table
    * **header**: The part is the name of a column in the table
    * **input**
    * **NA**: The part is not applicable to the table
* **<table_name>Required**: Used to indicate whether a column is mandatory for a table

    Can have one of the following values:
    * **mandatory**: The column is mandatory
    * **optional**: The column is not mandatory
    * **NA**: The column is not applicable


An example parts dictionary argument is shown below,

```python
{
    "parts": [
        {
            "partID": "addresses",
            "partType": "table",
            "addresses": "NA",
            "addressesRequired": "NA",
            "contacts": "NA",
            "contactsRequired": "NA"
        },
        {
            "partID": "contacts",
            "partType": "table",
            "addresses": "NA",
            "addressesTable": "NA",
            "contacts": "NA",
            "contactsRequired": "NA"
        }
        {
            "partID": "addressID",
            "partType": "attribute",
            "addresses": "PK",
            "addressesRequired": "mandatory",
            "contacts": "NA",
            "contactsRequired": "NA"
        },
        {
            "partID": "addL2",
            "partType": "attribute",
            "addresses": "header",
            "addressesRequired": "optional",
            "contacts": "NA",
            "contactsRequired": "NA"
        },
        {
            "partID": "contactID",
            "partType": "attribute",
            "addresses": "NA",
            "addressesRequired": "NA",
            "contacts": "PK",
            "contactsRequired": "NA"
        }
    ]
}
```

The generated cerberus object is shown below,

```python
{
    "addresses": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
                    "required" True,
                    "meta": {
                        "partID": "addressID",
                        "addresses": "PK",
                        "addressesRequired": "mandatory",
                    }
                },
                "addL2": {
                    "meta": {
                        "partID": "contactID",
                        "contacts": "PK",
                        "contactsRequired": "NA"
                    }
                }
            },
            "meta": {
                "partID": "addresses",
                "partType": "table"
            }
        }
    },
    "contacts": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "contactID": {
                    "required": True,
                    "meta": {
                        "partID": "contactID",
                        "ContactTable": "PK",
                        "ContactTableRequired": "mandatory"
                    }
                }
            }
        },
        "meta": {
            "partID": "contacts",
            "partType": "table"
        }
    }
}
```

The data dictionary columns that should be included in the `meta` field are:
* partID
* <table_name>Table
* <table_name>Required
