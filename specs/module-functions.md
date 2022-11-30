# validate_data

Validates an ODM dataset.

## Arguments

1. `data`: The ODM data to be validated.

    * `type`: A Python dictionary whose keys are the names of the tables as contained in the ODM data dictionary and values is a list containing the table rows.

        Example

        ```python
        {
            "addresses": [
                {
                    "addressID": "WastewaterSiteOttawa",
                    "addL1": "123 Laurier Avenue",
                    "addL2": "",
                    "city": "Ottawa",
                    "country": "Canada",
                    "datasetID": "",
                    "stateProvReg": "Ontario",
                    "zipCode": "KE2 TYU"
                }
            ],
            "contacts": [
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

2. `validation_rules`: The rules to validate the data against. This is a dictionary that contains a [cerberus](https://docs.python-cerberus.org/en/stable/) schema object, as well as the odm-version it's based on. The cerberus schema object should ideally be generated using the `generate_validation_schema` function.

    `type`: A Python dictionary with the following fields

    * `schemaVersion`: string that has a semver version
    * `schema`: [Cerberus schema](https://docs.python-cerberus.org/en/stable/schemas.html)

        Example

        ```python
        {
            "schemaVersion": "1.2.3",
            "schema": {
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
                        }
                    }
                }
            }
        }
        ```

## Return

Returns a dictionary with the found errors and warnings.

All errors and warnings for each validation rule are documented in the [specification for each validation rule](../validation-rules/).

* type: A Python dictionary consisting of the following fields
    * `odmDataVersion`: string consisting of the version of the ODM data
    * `validationSchemaVersion`: string consisting of the version of the validation schema used
    * `validationPackageVersion`: string consisting of the version of the validation package used
    * `errors`: A list of Python dictionaries describing each error. For more information refer to the files in the [validation-rules](../validation-rules/) folder
    * `warnings`: A list of Python dictionaries describing each warning.

# generate_validation_schema

Generates the cerberus schema containing the validation rules to be used with the `validate_data` function.

## Arguments

1. `odm_data_dictionary`: The ODM data dictionary [excel sheet](https://github.com/Big-Life-Lab/PHES-ODM/tree/V2-first-draft/template)

    * `type`: A dictionary whose keys are the sheet names and values is a list containing the sheet rows. Currently only the parts sheet is required.

        Example

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

2. `version`: The version of the ODM dictionary the cerberus schema is for

    * `type`: A string representing the version of the ODM to use

3. `schema_additions`: Optional argument which allows the user to update the cerberus schema with additional validations

    * `type`: A dictionary containing the updates. The shape is shown below,

    ```python
    {
        # The name of the table whose validation rules to update
        "<table_name>": {
            # The name of the column whose validation rules to update
            "<column_name>": {
                # Adds or updates the allowed rule for this column
                "[allowed]": string[]
            }
        }
    }
    ```

## Return

Return a dictionary that contains a valid cerberus schema object, as well as the odm-version it's based on. Values from the ODM data dictionary will also be added to the `meta` field for debugging purposes.

Example

```python
{
    "schemaVersion": "1.2.3",
    "schema": {
        "addresses": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "addressID": {
                        "required" True,
                        "meta": [
                            {
                                "ruleId": "missing_mandatory_column",
                                "meta": [
                                    {
                                        "partID": "addressID",
                                        "addresses": "PK",
                                        "addressesRequired": "mandatory",
                                    }
                                ]
                            }
                        ]
                    },
                },
                "meta": {
                    "partID": "addresses",
                    "partType": "table"
                }
            }
        }
    }
}
```

## Logic

### Working with the `version` parameter

The cerberus schema for a part should be added only if it is active for the provided `version` argument. To see whether a part is valid for a version, the `status`, `firstReleased`, and `lastUpdated` fields are used.

* The `status` field can take one of two values, `active` or `depreciated`. `active` says that a part is currently being actively used while `depreciated` says the opposite.
* The `firstReleased` and `lastUpdated` fields has the version of the ODM when the part was first added and last changed respectively.
* The `changes` field is used to describe the changes made from one version to another.

The validation metadata for a part should only be used if it was active for the version in the `version` argument.

Example of two parts from dictionary version 2.

```python
{
    "parts": [
        {
            "partID": "addresses",
            "label": "Address table",
            "partType": "table",
            "addresses": "NA",
            "addressesRequired": "NA",
            "status": "active",
            "changes": "added in version 2",
            "firstReleased": "2",
            "lastUpdated": "2"
        },
        {
            "partID": "comp3",
            "label": "Composite grab sample of 3",
            "partType": "category",
            "addresses": "NA",
            "addressesRequired": "NA",
            "status": "depreciated",
            "changes": "Use grab with collection number (collectNum) = 3",
            "firstReleased": "1",
            "lastUpdated": "2"
        }
    ]
}
```

* The addresses part is currently active (status = 'active') and should only be included in version 2 since it was first released (firstReleased = '2') then.
* The `comp3` part was depreciated in version 2 (status = 'depreciated' and lastUpdated = '2') and should only be included in version 1 (firstReleased = '1')

Version 2 of the dictionary renamed certain part pieces, for example, the `WWMeasures` table was renamed to `measures` in version 2. To be backcompatible with version 1, columns were added to the parts list to document their version 1 equivalents. These columns are documented where necessary in the spec.

## Working with the schema_additions

Currently, the function only supports updating the following cerberus validation rules,

* [allowed](https://docs.python-cerberus.org/en/stable/validation-rules.html#allowed)

For example, for the following set of arguments to the function,

```python
odm_data_dictionary = [
    {
        "partID": "sites",
        "partType": "table",
        "sites": "NA",
        "sitesRequired": "NA"
    },
    {
        "partID": "siteID",
        "partType": "attribute",
        "sites": "pK"
        "sitesRequired": "mandatory"
    }
]

version = "2.0.0"

schema_additions = {
    "sites": {
        "siteID": {
            "allowed": ["Ottawa Site", "Montreal Site"]
        }
    }
}
```

The corresponding validation schema should be,

```python
{
    "schemaVersion": "2.0.0",
    "schema": {
        "sites": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "siteID": {
                        "required" True,
                        "allowed": ["Ottawa Site", "Montreal Site"],
                        "meta": [
                            {
                                "ruleId": "missing_mandatory_column",
                                "meta": [
                                    {
                                        "partID": "siteID",
                                        "sitesRequired": "mandatory"
                                    }
                                ]
                            }
                        ]
                    }
                }
            },
            "meta": {
                "partID": "sites",
                "partType": "table",
            }
        }
    }
}
```

Care should be taken to perform an update and not an overwrite of the `allowed` field if the schema already contains an `allowed` field for that column. For example for the arguments below,

```python
odm_data_dictionary = [
        {
            "partID": "samples",
            "partType": "table",
            "samples": "NA",
            "dataType": "NA",
            "catSetID": "NA"
        },
        {
            "partID": "collection",
            "partType": "attribute",
            "samples": "header",
            "dataType": "categorical",
            "catSetID": "collectCat"
        },
        {
            "partID": "comp3h",
            "partType": "category",
            "samples": "input",
            "dataType": "varchar",
            "catSetID": "collectCat"
        },
        {
            "partID": "comp8h",
            "partType": "category",
            "samples": "input",
            "dataType": "varchar",
            "catSetID": "collectCat"
        },
        {
            "partID": "flowPr",
            "partType": "category",
            "samples": "input",
            "dataType": "varchar",
            "catSetID": "collectCat"
        }
]

version = "2.0.0"

schema_additions = {
    "samples": {
        "collection": {
            "allowed": ["comp3", "comp3dep"]
        }
    }
}
```

The corresponding validation schema would be,

```python
{
    "schemaVersion": "2.0.0",
    "schema": {
        "samples": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "collection": {
                        "allowed": ["comp3h", "comp8h", "flowPr", "comp3", "comp3dep"],
                        "meta": [
                            {
                                "ruleId": "invalid_category",
                                "meta": [
                                    {
                                        "partID": "collection",
                                        "samples": "header",
                                        "dataType": "categorical",
                                        "catSetID": "collectCat"
                                    },
                                    {
                                        "partID": "comp3h",
                                        "partType": "category",
                                        "catSetID": "collectCat"
                                    },
                                    {
                                        "partID": "comp8h",
                                        "partType": "category",
                                        "catSetID": "collectCat"
                                    },
                                    {
                                        "partID": "flowPr",
                                        "partType": "category",
                                        "catSetID": "collectCat"
                                    }
                                ]
                            }
                        ]
                    }
                }
            },
            "meta": {
                "partID": "samples",
                "partType": "table",
            }
        }
    }
}
```