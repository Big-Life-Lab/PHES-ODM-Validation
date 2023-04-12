# Changelog

## [0.4.0] - 2023-04-11

### General

- Added parameter to validate_data function for specifying spreadsheet input
- Added rule blacklist for disabling individual rules
- Added support for the final ODM v2.0.0 release
- Changed error report message format, to make it more consistent
- Fixed docs, parts and schemas

### Spreadsheet validation

- Fixed redundant coercion warnings (from string to other types)
- Fixed redundant column errors
- Fixed row numbers in the error report so that they match Excel

### Excel validation tool

- Fixed writing of empty error/warning files
- Changed output dir for csv files to decrease clutter

### Validation schemas

#### v1.1.0

- Added AssayMethod.unit.allowed
- Added SiteMeasure.siteID.maxlength
- Added WWMeasure.siteID.maxlength
- Changed Sample.pooled.allowed to [False, True]
- Removed Site.siteID
- Removed Site.type.allowed.wwtpMuS
- Removed WWMeasure.fractionAnalyzed.allowed
- Removed WWMeasure.index.coerce
- Removed WWMeasure.type.allowed

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

- Added Sample.collection.allowed
- Added SiteMeasure
- Added WWMeasure.fractionAnalyzed.allowed
- Changed Sample.pooled.allowed
- Removed AssayMethod.aggregation
- Removed AssayMethod.instrumentID
- Removed AssayMethod.organization
- Removed AssayMethod.type
- Removed AssayMethod.updateDate
- Removed Instrument.index
- Removed Instrument.organization
- Removed Instrument.updateDate
- Removed Lab.organization
- Removed Lookup
- Removed Polygon.organization
- Removed Polygon.referenceLink
- Removed Polygon.updateDate
- Removed Sample.organization
- Removed Sample.siteID
- Removed Sample.updateDate
- Removed Site.organization
- Removed Site.polygonID
- Removed Site.updateDate
- Removed WWMeasure.dateTime
- Removed WWMeasure.organization
- Removed WWMeasure.polygonID
- Removed WWMeasure.referenceLink
- Removed WWMeasure.sampleID
- Removed WWMeasure.siteID
- Removed WWMeasure.updateDate
