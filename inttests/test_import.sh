#!/bin/bash

# XXX: must be run with lowest required python version (as specified in
# pyproject.toml), to ensure compatibility

set -ex

[[ "$(python --version)" == "Python 3.8."* ]]

repo=$(dirname $(realpath $0))/..
url="git+file://$repo"
dir=$(mktemp -d)

cd $dir
python -m venv .env
source .env/bin/activate

pip install $url
python -c "from odm_validation.validation import validate_data"
