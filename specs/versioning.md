# Versioning

This document will go over how versioning will work for the ODM validation package. Broadly, versioning refers to the process for releasing new versions of a product. Within the context of the ODM validation, versioning needs to take into account the following:

* The versioning for the validation schema files and 
* The versioning for the validation rules and the code used to implement them

## Validation Schema Versioning

An ODM user needs two pieces of information for validation, the ODM data they want to validate and the validation schema. Versioning for the validation schemas will follow ODM versioning i.e. for each version of the ODM there will be a corresponding validation schema. Practically, the files containing the validation schema for each ODM version will be stored within the validation package. A new version of the ODM will trigger the release of a new validation schema for that version in addition to a new version of the validation package containing the new validation schema file.

The release of a new validation schema should result in an increment of the patch version of the validation package since no breaking changes were made.

Since the ODM follows semver versioning, breaking changes are indicated by an increment of the minor or major version. The validation schema will also follow the same approach for example ODM data v 1.1.x will be compatible with all validation schema version v1.1.x.

## Validation Rules

The validation rules CSV sheet encodes metadata for all the active and inactive rules implemented by the package. The CSV sheet does not have its own versioning, but is tied to the versioning of the validation package, changes to the CSV sheet will lead to updates in either the validation schemas and/or the package. 

When a new validation rule is added, we need to decide which versions of the ODM the rule is compatible with. The [ODMVersion](../validation-rules//README.md/#adding-a-new-rule) field in the CSV file outlines which ODM versions the rule supported. 

The addition of a new rule should be followed by a minor version update of the validation package as well as an update to all supported validation schema files. The version of the validation schema files remains the same.

If a validation rule is updated, the version of the new release depends on if it is a breaking change or not. For example, changing the ID of a rule should result in a minor version change.

Finally, a validation rule can be deleted. The deletion of a rule is signified by an update to the [status](../validation-rules/README.md/#adding-a-new-rule) field to "inactive". A rule deletion should follow the same update process as a rule addition.

## Validation Source Code

Changes to the source code should trigger a validation package version change. The version of the new release depends on if its a breaking change or not.

# Conclusion

Versioning of the validation package needs to take into account not only the source code for the package but also changes to the validation schema files which in turn depends on changes to the ODM. Finally, since an update to the validation schema file can take place without an update to its version, for example if the validation rules are updated, to debug an issue the following pieces of information are required:

1. The version of the ODM data being validated
2. The version of the validation schema used and
3. The version of the validation package used


