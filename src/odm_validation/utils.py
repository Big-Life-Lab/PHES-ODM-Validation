import inspect
import os
import sys
from os.path import join, splitext
from pathlib import Path

import csv
import json
import yaml


def get_pkg_dir() -> str:
    '''returns the actual pkg. dir or `/src/odm_validation/` if in dev. env.'''
    # this module file is located directly under the pkg. dir, so we can lookup
    # its path and use that directly
    mod = sys.modules[__name__]
    mod_path = inspect.getfile(mod)
    mod_dir = os.path.dirname(mod_path)
    return mod_dir


def get_asset_dir() -> str:
    pkg_dir = get_pkg_dir()
    asset_dir = join(pkg_dir, 'assets')

    # If the `asset_dir` path doesn't exist, then we can assume that the
    # package hasn't been installed, but is used directly in a development
    # environment, meaning that we need to specify the path as it is in the
    # repo.
    if not os.path.isdir(asset_dir):
        root_dir = Path(pkg_dir).parent.parent
        asset_dir = join(root_dir, 'assets')

    return asset_dir


def import_csv_file(path: str) -> list[dict]:
    result = []
    with open(path, newline='', encoding='utf8') as f:
        for row in csv.DictReader(f):
            result.append(row)
    return result


def import_json_file(path: str) -> dict:
    with open(path, 'r') as f:
        return json.loads(f.read())


def import_yaml_file(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def export_yaml_file(data: dict, path: str):
    with open(path, "w") as f:
        return f.write(yaml.dump(data))


def import_dataset(path: str) -> dict:
    # print('importing ' + path)
    _, ext = splitext(path)
    if ext == '.csv':
        return import_csv_file(path)
    elif ext == '.json':
        return import_json_file(path)
    elif ext == '.yml':
        return import_yaml_file(path)
    else:
        assert False, f'unknown dataset extension "{ext}"'
