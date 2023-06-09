"""Global settings/constants.

These are global to avoid passing them all over the code. This is safe
as long as they are only mutated by the user of the library.
"""

BATCH_SIZE = 100
"""The number of rows to batch together when validating."""

VERBOSITY: int = 2
"""The validation error message verbosity."""
