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