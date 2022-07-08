from cerberus import Validator
schema = {'name': {'type': 'string'}, 'age': {'type': 'integer', 'min': 10}}
document = {'name': 'Little Joe', 'age': 5}
v = Validator(schema)
v.validate(document)
print(v.errors)
