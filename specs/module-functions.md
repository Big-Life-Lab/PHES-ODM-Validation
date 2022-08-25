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

2. `validation_rules`: The rules to validate the data against. This is a [cerberus](https://docs.python-cerberus.org/en/stable/) schema object which should ideally be generated using the `generate_cerberus_schema` function. 

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

Returns True if the the data had no validation errors.

Returns an error object that describes all the failed validations. The type is shown below:

* type: A Python dictionary consisting of the following fields
    * `odmDataVersion`: string consisting of the version of the ODM data
    * `validationSchemaVersion`: string consisting of the version of the validation schema used
    * `validationPackageVersion`: string consisting of the version of the validation package used
    * `errors`: A list of Python dictionaries describing each error. For more information refer to the files in the [validation-rules](../validation-rules/) folder

# generate_cerberus_schema

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

## Return

Return a dictionary that is a valid cerberus schema object. In addition, values from the ODM data dictionary will also be added to the `meta` field for debugging purposes. 

Example

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

## Logic

### Working with the `version` parameter

The cerberus schema for a part should be added only if it is active for the provided `version` argument. To see whether a part is valid for a version, the `status`, `firstReleased`, and `lastUpdated` fields are used.

* The `status` field can take one of two values, `active` or `deprecitate`. `active` says that a part is currently being actively used while `deprecitate` says the opposite.
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
            "status": "deprecitate",
            "changes": "Use grab with collection number (collectNum) = 3",
            "firstReleased": "1",
            "lastUpdated": "2"
        }
    ]
}
```

* The addresses part is currently active (status = 'active') and should only be included in version 2 since it was first released (firstReleased = '2') then.
* The `comp3` part was deprecitated in version 2 (status = 'deprecitate' and lastUpdated = '2') and should only be included in version 1 (firstReleased = '1')

Version 2 of the dictionary renamed certain part pieces, for example, the `WWMeasures` table was renamed to `measures` in version 2. To be backcompatible with version 1, columns were added to the parts list to document their version 1 equivalents. These columns are documented where necessary in the spec.
