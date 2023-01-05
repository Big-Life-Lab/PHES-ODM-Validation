# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PHES-ODM Validation'
copyright = '2022, OHRI'
author = 'OHRI'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',  # markdown
    'nbsphinx',  # jupyter notebooks
    'sphinx.ext.autodoc',  # python code
]

source_suffix = [
    '.md',
    '.rst',
]

exclude_patterns = [
    '**.ipynb_checkpoints',
    'README.md',
    'validation-rules/_setup.md',
    'build',
]

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#
add_module_names = False

# -- MyST extension ----------------------------------------------------------

myst_gfm_only = True  # enable compliance only with GitHub-flavored Markdown

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_theme_options = {
    'page_width': '975px',  # to make the API page wide enough to be readable
}
html_static_path = ['_static']
html_logo = os.path.join(html_static_path[0], 'ODM-logo.png')
