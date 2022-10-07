import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from cerberus import Validator

validator = Validator({"name": {
                "type": "string",
                "empty": False
}
})

validator.validate({"name": "  "})

print(validator.errors)
