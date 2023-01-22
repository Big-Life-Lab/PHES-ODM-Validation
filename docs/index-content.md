The validation toolkit for the [Population Health Environmental Surveillance Open Data Model (PHES-ODM)](https://github.com/Big-Life-Lab/PHES-ODM) ensures your ODM data is complete and interoperable. Users can check whether their data meets the ODM dictionary format.

# At a glance

Validation is performed based on a set of rules defined in a schema. The `validate_data` function is used to perform the validation on `data` with the `schema` specified.

```python
schema = import_schema("schema.yml")
errors = validate_data(schema, data)
```

# Overview

There are three parts to the ODM validation toolkit.

1. **Python functions to validate ODM-formatted data**. These functions check ODM data for missing, incomplete, or incompatible data. The functions return a list of errors and warnings.
1. **A list of validation rules**. The rules define what are valid ODM data. Examples of rules include [mandatory data feids](insert the link to the missing*mandatory_column rule) and valid data types. For example, every measurent must have a date the mesaurment was preformed, and the [date type](insert the link to data type rule) must follow [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) format. Rules are combined together in a \_validation schema*.
1. **A standard schema method**. The validation toolkit extends the [cerebrus](https://docs.python-cerberus.org/en/stable/index.html) validation method to provide a standard approach to defining validation rules that allows the rule list to be easily extended. For example, a wastewater surveillance program can can generate a list of the sample sites within their program; and then use the ODM validation toolkit to ensure all their data include a `siteID` with a valid idenfitication. See [tutorial X]() for how to extend the ODM schema.

# Installation

@zargot please add

# Usage

Quick 'how to' - defined as the steps to solve a specific problem. These compliment our tutorials that are learning oriented documentation for newcommers.

## Validate a specific ODM version

## Validate with you own schema

## Generate a schema from the ODM dictionary

You can genereate your own schema directly from the ODM parts table.

```python
parts = import_dataset("parts.csv")
schema = generate_cerberus_schema(parts)
errors = validate_data(schema, data)
```

## Make you own validation rule

{example of validating a list of siteIDs}

# Fequently asked questions and support

Get support on the [ODM Discourse community forum](https://odm.discourse.group/c/support). Use the `#validate` in your question. Use the `#faq` and `#validate` to find frequently asked questions.

See [Contributing][link] for how to suggest a new rule.

Error or bugs can be reported on GitHub [Issues](https://github.com/Big-Life-Lab/PHES-ODM-Validation/issues).
