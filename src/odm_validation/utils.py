from os.path import splitext

import csv
import json
import yaml

from odm_validation.schemas import Schema


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


def import_dataset(path: str) -> Schema:
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


def import_schema(path: str) -> Schema:
    return import_yaml_file(path)


def export_schema(schema: Schema, path: str):
    export_yaml_file(schema, path)
