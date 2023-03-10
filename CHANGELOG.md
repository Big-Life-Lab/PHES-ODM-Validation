# Changelog

## [0.3.0] - 2023-03-10

### General

- Changed license to CC BY 4.0
- Fixed mapping of tables/attributes in ODM v1
- Fixed parts and schemas

### Excel validation tool

- Addded a summary output file
- Fixed sheet name detection
- Fixed a bug where spreadsheets with many empty lines slowed down validation

### Validation schemas

#### v1.1.0

- Added a category validation rule for the `collection` column in `Sample`
- Added `SiteMeasure`
- Added a category validation rule for the `fractionAnalyzed` column in `WWMeasure`
- Removed the following columns from `WWMeasure`
    - dateTime
    - organization
    - polygonID
    - referenceLink
    - sampleID
    - siteID
    - updateDate
- Updated the allowed categories for the `pooled` column in `Sample`
    - Removed the `detected` category
    - Added a `accessToLocalHA` category
- Removed the following columns from the `AssayMethod`
    - aggregation
    - instrumentID
    - organnization
    - type
    - updateDate
- Removed the following columns from `Instrument`
    - index
    - organization
    - updateDate
- Removed the `organization` column from `Lab`
- Removed the `Lookup` table
- Removed the following columns from `Polygon`
    - organization
    - referenceLink
    - updateDate
- Removed the following columns from `Sample`
    - organization
    - siteID
    - updateDate
- Removed the following columns from `Site`
    - organization
    - polygonID
    - updateDate
