# validate_data

Validates an ODM dataset.

## Arguments

1. `data`: The ODM data to be validated.

    `type`: A Python dictionary whose keys are the names of the tables as contained in the ODM data dictionary and values is a list containing the table rows.

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

    `type`: [Cerberus schema](https://docs.python-cerberus.org/en/stable/schemas.html)

    Example

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
                }
            }
        }
    }
    ```

## Return

Returns True if the the data had no validation errors.

Returns an errors report of the validation failed. The error report is a list of dictionaries with each dictionary providing information on a specific error type. All error types can be seen in the validation-rules folder.

# generate_cerberus_schema

Generates the cerberus schema containing the validation rules to be used with the `validate_data` function. 

## Arguments

1. `odm_data_dictionary`: The ODM data dictionary [excel sheet](https://github.com/Big-Life-Lab/PHES-ODM/tree/V2-first-draft/template)

    `type`: A dictionary whose keys are the sheet names and values is a list containing the sheet rows. Currently only the parts sheet is required.

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

## Validating rules based on dictionary version

Validation rules are applied only to parts and lists with the 'status' property is 'active'.

Example of two parts from dictionary Version 2.

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
            "lastUpdated": "1"
        }
    ]
}
```

Include `addresses` in validation rules for Version 2.
Exclude `comp3` in valation rules for Version 2, but include this part for validation rules in version 1.

The example above shows the four parts and lists properties to support versioning:

- `status` - The status of the part or list. 'active' means the part is used in the dictionary version. 'depreciated' means the part has been retired and not longer used in the version.
- `firstReleased` - he version that the the part or set was first released.
- `lastUpdated` - The date that the part was last updated.
- `changes` - A description of the changes to the part of list from the previous version.

### Validating rules prior to version 1

The ODM validator was developed for Version 2, but with the ability to validate ODM Version 1.1 data. There are several properties in Version 2.0 parts to assist the development of Version 1 rules. These include:

- `version1Table` - The version 1 report table where values for the part were recorded. In Version 1, `variables` and `variableCategories` were moved to `parts`.
- `version1Location` - The table which the part appears in Version 1. There are three tables in Version 1: `variables`, `variableCategories` and `tables`. Thes parts within these tables were all moved to `parts` in Version 2. In Version 2, `variables` are identified as `partType = measure, meathod, or attribute`. Tables`are identified as`partType = table`.
- `version1Variable` - The variable identifier in Version 1. A Version 1 variable is the equivalent of a `partType = method, measure, or attribute` in Version 2.
- `version1Category` = The category identifier in Version 1. A Version 1 category is the equivalent a Version 2 part with `partType = category`.
- `version1to2Changes` = A descript of changes from Version 1 to Version 2.
