# Population Health and Envirmental Open Data Model (PHES-ODM) Validation Toolkit

The PHES-ODM validation toolkit allows users to check whether their data meets the ODM dictionary format.

## At a Glance

You invoke the PHES-ODM validator to check whether your wastewater or other environmental data meets the ODM format. You get back a report that indicates any errors or ommisions in the data format.

For example, `measureID` is a required field that used record the name of measures and observations such as Covid-19 RT-qPCR results.

**Rule list**

```
RuleID: 1
name: "Missing required column"
Description: "Validate the column names in a data table."
messageType: "Error"
messageText: "Missing Required Column: "
notes: "This rule is used to validate that the rows in a table have all their mandatory
columns. For each table in the data argument, the metadata for this rule is present
in the parts sheet in the partID, <table_name>Table, and <table_name>Required column."
```

**Example MeasureReport table**
|measure|reportDate|value|unitID|aggreationID|
|---------|----------|-----|------|------------|
|covN1 |2022-07-13|23 |gcMl |single |

**Validation report**

```
{
    "error": "Missing Required Column",
    "tableName": "MeasureReport"
    "columnName": "measureID"
}
```

Fix this error by changing the header name from `measure` to `measureID`

```
{
    "error": none
}
```

## Overview

Validation can be performed throughout the data life cycle. Measurement laboratories can validate their data before sharing data with repositories or other researchers. Data repositories can validate data when they accept data from laboratories. Public health epidemiologists and modellers can validate data before analysis.

The emphasis of ODM validation is on providing guidance and support. When you validate data, you receive a report with warnings and errors. ODM validation emphasizes warnings rather than errors. An example of a warning is when an email does not contain an '\@' symbol.

## The toolkit

The ODM validation toolkit is comprised of:

1. **rule list** (/assets/validation-rules/validation-rules-list.csv) - A list and description of all rules, along with additional metadata such as the warning or error message.
2. **rule documentation** (/validation-rules/) - Details and examples of the rules.
3. **rule validation module** (odmvalidator) - a python package that contains functions to validate ODM data.
4. **rule schema**: These are the files that encode the validation rules executed by the Python code. All files are stored in the **assets/validation-schemas** folder with each file corresponding to a version of the ODM. The contents of the file has the version of the schema being used as well as the actual schema.
5. **reference documents (location?)** - Additional documents describing rules. Examples of validation rules include validating measure data types (e.g. integer, string), ranges (e.g. number between 0 and 100), uniqueness (e.g. sample ID is not repeated).

Many rules are defined in the ODM parts and sets tables. For example, the parts table includes the data type for each measure. The sets tables lists units and aggregations that are allowed for each measure. The parts table also includes what headers are included in the manadtory and optional headers in ODM report tables.

The _odmvalidator_ is the main workhorse within the toolkit. This program code accepts a ODM data and a schema and returns a validation report. We created _odmvalidator_ as an open-source python package that can be incorporated into a full range of information systems (i.e. ArgGIS, Microsoft 365, custom laboratory management information systems or data repositories). As a python package, data can be easily validated when it is stored a range of formats (CSV, Excel, SQL database).

Underdevelopment is a publicly available web application that implements the toolkit, including the odmvalidator.

## Installation

```
git clone https://github.com/Big-Life-Lab/PHES-ODM-Validation.git odm-validation
cd odm-validation
pip install src/odm-validation
```
