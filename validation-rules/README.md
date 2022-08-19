# Validation rules

Validation rules are the set of rules that the ODM validation module uses to assess wehther data confirms to the ODM dictionary. The module uses Python [functions](../module-functions.md). The full list of validation rules natively supported by the ODM can be seen in the validation rules list CSV file in [metadata/validation-rules-list.csv](../../metadata/validation-rules-list.csv).

Each rule in the validation-rules-list.csv has an `ruleID`. There is a corresponding markdown document for each validataion rule that can be found in [/validation-rules/](../../valiation-rules/). For example, the ruleID = `MissingMandatoryColumn` has a file `MissingMandatoryColumn.md`. The markdown document for each rule includes:

1. A description of the rule.
2. One or more examples of the rule.
3. The error report returned to the user when the rule is violated.
4. The parts of the data dictionary that contain the metadata required to implement, if the rule medata data is in the data dictionary.
5. Reference to additional metadata, if needed.
6. The logic about how to convert the rule metadata into the rule schema (a [Cerberus schema](#the-base-cerberus-schema)).
7. An example of the Cerberus schema.

## Adding a new rule

The ODM is accepts new validation rules that are developed by users. As you can use the instructions below to generate custom validation rules for your own surveillance program that can be executed using the python functions in xxx package. If you are new to GitHub you can get help by requesting a new validation rule on [GitHub Issues](https://github.com/Big-Life-Lab/PHES-ODM-Validation/issues) or the [ODM community discussion board](https://odm.discourse.group).

The steps to request or generate a new rule are:

1. Fork this Github repository and make a branch from `rules`.

   1.1. Name the branch: request/[ruleID]. The rule ID is a unique ID that will be used for your rule (use CascalCase). For example, if you named your new rule, `MyAmazingRule`, the new branch for this rule would be: `request/MyAmazingRule`.

   1.2. You'll make a PR to the `rules` branch after you generate your rule files and documentation.

2. Add a new file at a new row at the bottom of [metadata/validation-rules-list.csv](../../metadata/validation-rules-list.csv) folder containing details about your new rule. These details should include:

   2.1. `ruleId`: The unique identifier for your rule
   2.2. `label`: A short description
   2.3. `description`: A long description
   2.4. `messageType`: Whether this rule generates an error or a warning. The valid values are `error` and `warning`
   2.5. `messageText`: The error message to display. Placeholders can be placed by using <> for example <table_name>
   2.6. `status`: Whether this rule is active. Valid values are `active` and `inactive`
   2.7. `firstReleased`: Version of the validation module when this rule will be added. Uses semver versioning.
   2.8. `added`: The date when it was created
   2.9. `lastUpdated`: The date when it was updated
   2.10. `changes`: The list of changes
   2.11. `notes`

3. Identify metadata required for the rule.

   3.1. If rule is uses metadata from the ODM dictionary - include the include the parts of the ODM data dictionary that contains the metadata for your rules along with the logic for converting them to a cerberus schema. See information about the Cerberus schema below.
   3.2. If your rule contains other metadata - generate a Cerberus schema (see below) with the metadata or review and copy existing rules that have similar metadata as your rule. If you need help, make a GH issue or make at post on discussion board if you cannot file a similar rule (use tag...)

4. Describe the validation process. The simplest method is to create a copy and modify [validation-rules/MissingMandatoryColumn.md](MissingMandatoryColumn.md).

5. Add a Cerberus schema, if possible. Generating a Cerberus schema can be challenging if you have not previously created one. The ODM development team will help, but team needs a clear description and examples in your 'MyAwesomeRule.md' file. Further,
   5.1. You do not need to add Cerberus schema if your rule uses only data from the `partscsv`. The ODM development team will genereate a schema for your rule.
   5.2. You can create a Cerebus schema by modifying existing Cerebus schemas from an existing rule markdown document. A brief description of the base Cereberus schema is below and there are more details on the [Cerberus website](https://docs.python-cerberus.org/en/stable/schemas.html).

## The base Cerberus schema

The ODM uses the [cerberus](https://docs.python-cerberus.org/en/stable/schemas.html) schema to execute validation rules. A validation schema is a dictionary whose keys are the names of the tables as specified in the ODM and whose values contains the schema for the table. To generate a new rule, you provide a description and example of the data validation, which is then used to generate a Cerberus validation schema.

For example, list of table names can be retreived by looking at the `partID` and the `partType` column in the dictionary. A `partType` value of `table` implies that the corresponding part in the `partID` column is the name of a table. For example, consider the following ODM dictionary,

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

### Version 1

The following columns are used to backport from version 2 of the ODM to version 1,

* **version1Location**: Where in version 1 the part belongs to. The possible values are `tables`, `variables`, or `variableCategories`.
* **version1Table**: The name of the table in version 1
* **version1Variable**: The name of the table variable in version 1
* **version1Category**: The name of the variable category in version 1

As mentioned above, the table name is encoded in the `version1Table` column. If a table part has a version 1 equivalent, then this column will have a value, otherwise it will be empty. For example, consider the ODM snippet below,

```python
{
    "parts": [
        {
            "partID": "addresses",
            "partType": "table",
            "version1Table": "addresses",
            "version1Location": "tables"
        },
        {
            "partID": "contacts",
            "partType": "table",
            "version1Table": "",
            "version1Location": "tables"
        },
        {
            "partID": "measures",
            "partType": "table",
            "version1Table": "",
            "version1Location": "WWMeasure;SiteMeasure;CovidPublicHealthData"
        }
    ]
}
```

The corresponding cerberus schema for version 1 of the ODM would be,

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
            "partType": "table",
            "version1Table": "addresses",
            "version1Location": "tables"
        }
    },
    "WWMeasure": {
        "type": "list",
        "schema": {
            "type": "dict",
            # The remaining schema fields are filled using the rest of the dictionary
        },
        "meta": {
            "partID": "measures",
            "partType": "table",
            "version1Table": "",
            "version1Location": "WWMeasure; SiteMeasure;CovidPublicHealthData"
        }
    },
    "SiteMeasure": {
        "type": "list",
        "schema": {
            "type": "dict",
            # The remaining schema fields are filled using the rest of the dictionary
        },
        "meta": {
            "partID": "measures",
            "partType": "table",
            "version1Table": "",
            "version1Location": "WWMeasure; SiteMeasure;CovidPublicHealthData"
        }
    },
    "CovidPublicHealthData": {
        "type": "list",
        "schema": {
            "type": "dict",
            # The remaining schema fields are filled using the rest of the dictionary
        },
        "meta": {
            "partID": "measures",
            "partType": "table",
            "version1Table": "",
            "version1Location": "WWMeasure; SiteMeasure;CovidPublicHealthData"
        }
    }
}
```

Notice how the last part in the list corresponds to three tables in version 1, this will need to be taken into account.

To find the columns that are part of a table in version 1, we can use the `version1Location`, `version1Table`, and `version1Variable` columns. For example,

```python
{
    "parts": [
        {
            "partID": "instruments",
            "partType": "table",
            "version1Table": "Instrument",
            "version1Location": "tables",
            "version1Variable": ""
        },
        {
            "partID": "model",
            "partType": "attribute",
            "version1Table": "Instrument",
            "version1Location": "variables",
            "version1Variable": "model"
        }
    ]
}
```

implies that the version 1 table `Instrument` has a column called `model` in it.

