The PHES-ODM validation toolkit allows users to check whether their data meets the ODM dictionary format.

# At a glance

Validation is performed based on a set of rules defined in a schema. The `validate_data` function is used to perform the validation on `data` with the `schema` specified.

```python
schema = import_schema("schema.yml")
errors = validate_data(schema, data)
```

The schema can also be generated directly from the ODM parts table.

```python
parts = import_dataset("parts.csv")
schema = generate_cerberus_schema(parts)
errors = validate_data(schema, data)
```
