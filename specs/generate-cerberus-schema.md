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
```

# Features

This section will go over the validation features in the [specification for the `validate_data` function](./validate-data.md), and specify the creation of the cerberus object for it. The final result of the function is a cerberus object that is a combination of all the objects specified in each sub-section below.

## MissingMandatoryColumn

The ODM dictionary fields used to generate the cerberus object for this rule are:

* **partID**: Contains the name of the part
* **<table_name>Table**: Used to indicate whether thee part is a part of the table
    
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
        },
        {
            "partID": "contactID",
            "AddressTable": "NA",
            "AddressTableRequired": "NA"
            "ContactTable": "PK",
            "ContactTableRequired": "mandatory"
        }
    ]
}
```

The generated cerberus object is shown below,

```python
{
    "Address": {
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
    },
    "Contact": {
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
```

The data dictionary columns that should be included in the `meta` field are:
* partID
* <table_name>Table
* <table_name>Required
