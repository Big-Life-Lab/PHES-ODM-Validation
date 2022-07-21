This folder contains the specifications for all the validation rules currently supported by the ODM. Each file contains information about one rule which includes: 

1. How to convert the data dictionary rows into the cerberus schema for the rule and 
2. The error report returned to the user when the rule is violated.

At a high level, the cerberus object is a dictionary whose keys are the names of the tables as specified in the ODM and whose values contains the schema for the table. The list of table names can be retreived by looking at the `partID` and the `partType` column in the dictionary. A `partType` value of `table` implies that the corresponding part in the `partID` column is the name of a table. For example, consider the following ODM dictionary,

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
            # The remaining schema fields are filled using the rest of the dictionary
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
            #  The remaining schema fields are filled using the rest of the dictionary
        },
        "meta": {
            "partID": "contacts",
            "partType": "table"
        }
    }
}
```

# Adding a new rule

The ODM is open to adopting new validation rules. The steps to petition for a new rule are:

1. Create a PR contiaining the details for your new rule
2. Add a new file in the [specs/validation-rules](.) folder containing details about your new rule. These details should include:
    1. A unique ID for your new rule. The [validation-rules-list.csv](../../metadata/validation-rules-list.csv) contains all the currently supported validation rules and their IDs
    2. A description of your rule including examples of ODM data rows which will fail your rule and rows that will pass
    3. What the error report for a failed row will look like
    4. The parts of the ODM data dictionary that contains the metadata for you rules along with the logic for converting them to a cerberus schema
    The simplest method is to create a copy of the [missing-mandatory-column.md](./missing-mandatory-column.md) and modifying it
3. Add a new entry in the [validation rules list file](../../metadata/validation-rules-list.csv). The details about each column can be seen below:
    1. `ruleId`: The unique identifier for your rule
    2. `label`:  A short description
    3. `description`: A long description
    4. `messageType`: Whether this rule generates an error or a warning. The valid values are `error` and `warning`
    5. `messageText`: The error message to display. Placeholders can be placed by using <> for example <table_name>
    6. `status`: Whether this rule is active. Valid values are `active` and `inactive`
    7. `firstReleased`: Version of the validation module when this rule will be added. Uses semver versioning.
    8. `added`: The date when it was created
    9. `lastUpdated`: The date when it was updated
    10. `changes`: The list of changes
    11. `notes`  