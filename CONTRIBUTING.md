# Contributing

The PHES-ODM validation tool kit is an open source and community-driven. You can make suggestions for new validation rules or comment on existing rules on the PHES-ODM [discussion board](https://odm.discourse.group) or GitHub [Issues](https://github.com/Big-Life-Lab/PHES-ODM-Validation/issues).

## Adding a new rule

New validation rules can be requested by anyone ODM user. Instructions on how to add a new rule can be found in the [documentation](/rules.html#adding-a-new-rule). The validation rules [README.md](/rules.html) is a good source of additional information about how rules work.

## Code style

File structure:
[packaging.python.org/en/latest/tutorials/packaging-projects/](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

Style guide:
[peps.python.org/pep-0008](https://peps.python.org/pep-0008/)

### Additional rules

- Python and Markdown/Quarto files must use snake_case, other files and
  directories should use kebab-case.

  Rationale: Python modules are already required to be snake_case. Quarto files
  can also be thought of as code modules, and should be consistent with Python.
  Markdown files are basically the same as Quarto files, so they should have
  the same casing. Another (less important) reason is that the validation rules
  are implemented as Python functions (with snake_case), so it becomes more
  consistent if the rule specification files also have the same casing.
