# Context

One of the arguments of the `validate_data` function is a [cerberus](https://docs.python-cerberus.org/en/stable/) object containing the validation rules to apply to the data. This function will convert the metadata encoded in the ODM data dictionary into a cerberus object that can be used by the `validate_data` function.

# Function Signature

## Arguments

The function will take one argument, a dictionary containing the parts sheet from the ODM data dictionary. The sheet can be view [here](https://github.com/Big-Life-Lab/PHES-ODM/tree/V2-first-draft/template). An example is shown below,

```python
{
    "parts": [
        {
            "partID": "addressID",
            "label": "Address ID",
            "AddressTable": "PK",
            "AddressTableRequired": "mandatory"
        }
    ]
}
```

## Return

The function will return a dictionary that is a valid cerberus validation object. In addition, values from the ODM data dictionary will also be added to the `meta` field for debugging purposes. For example, the above dictionary example should generate the following cerberus object,

```python
{
    "Address": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
                    "required": True,
                    "meta": {
                        "partID": "addressID",
                        "AddressTable": "PK",
                        "AddressTableRequired": "mandatory"
                    }
                }
            }
        }
    }
}
```

# Features

This section will go over the validation features in the [specification for the `validate_data` function](./validate-data.md), and specify the creation of the cerberus object for it. The final result of the function is a cerberus object that is a combination of all the objects specified in each sub-section below.

At a high level, the cerberus object is a dictionary whose field names are the names of the table as specified in the ODM and whose field values contains the schema for that table, specified in the cerberus format. The list of table names can be retreived by looking at the `partID` and the `partType` column in the dictionary. A `partType` value of `hasTable`, `lookupTable`, or `reportTable` implies that the corresponding part in the `partID` column is the name of a table. For example, consider the following ODM dictionary,

```python
{
    "parts": [
        {
            "partID": "contact",
            "partType": "reportTable"
        },
        {
            "partID": "form",
            "partType": "lookupTable"
        }
    ]
}
```

The corresponding cerberus high level object would be,

```python
{
    "contact": {
        "type": "list",
        "schema": {
            "type": "dict",
            # Fill in the remaining schema fields using the rest of the dictionary
        }
    },
    "form": {
        "type": "list",
        "schema": {
            "type": "dict",
            # Fill in the remaining schema fields using the rest of the dictionary
        }
    }
}
```

The cerberus schema for each object is a list of dictionaries since that's how we expect the user to pass in their data in the validation function. The remaining headers in this section add on to this base object using the other fields in the dictionary.

## MissingMandatoryColumn

The ODM dictionary fields used to generate the cerberus object for this rule are:

* **partID**: Contains the name of a part
* **<table_name>Table**: Used to indicate whether the part is associated with a table
    
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
            "partID": "address",
            "partType": "reportTable",
            "addressTable": "NA",
            "addressTableRequired": "NA",
            "contactTable": "NA",
            "contactTableRequired": "NA"
        },
        {
            "partID": "contact",
            "partType": "reportTable",
            "addressTable": "NA",
            "addressTableRequired": "NA",
            "contactTable": "NA",
            "contactTableRequired": "NA"
        }
        {
            "partID": "addressID",
            "addressTable": "PK",
            "addressTableRequired": "mandatory",
            "contactTable": "NA",
            "contactTableRequired": "NA"
        },
        {
            "partID": "addL2",
            "addressTable": "header",
            "addressTableRequired": "optional",
            "contactTable": "NA",
            "contactTableRequired": "NA"
        },
        {
            "partID": "contactID",
            "addressTable": "NA",
            "addressTableRequired": "NA"
            "contactTable": "PK",
            "contactTableRequired": "mandatory"
        }
    ]
}
```

The generated cerberus object is shown below,

```python
{
    "Address": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "addressID": {
                    "required" True,
                    "meta": {
                        "partID": "addressID",
                        "AddressTable": "PK",
                        "AddressTableRequired": "mandatory",
                    }
                },
                "addL2": {
                    "meta": {
                        "partID": "addL2",
                        "AddressTable": "header",
                        "AddressTableRequired": "optional",
                    }
                }
            }
        }
    },
    "Contact": {
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
        }
    }
}
```

The data dictionary columns that should be included in the `meta` field are:
* partID
* <table_name>Table
* <table_name>Required
