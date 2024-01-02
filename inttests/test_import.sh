# run with the lowest required python version (as specified in pyproject.toml)

set -ex

repo=$(dirname $(realpath $0))/..
url="git+file://$repo"
dir=$(mktemp -d)

cd $dir
python -m venv .env
source .env/bin/activate

pip install $url
python -c 'from odm_validation.validation import validate_data'
