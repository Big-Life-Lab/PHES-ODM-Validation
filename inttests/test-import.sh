#!/bin/bash

# XXX: must be run with lowest required python version (as specified in
# pyproject.toml), to ensure compatibility

set -ex

[[ "$(python --version)" == "Python 3.9."* ]]

repodir=$(dirname $(realpath $0))/..
dir=$(mktemp -d)

cd $dir
python -m venv .env
source .env/bin/activate

pip install $repodir
python -c "from odm_validation.validation import validate_data"
