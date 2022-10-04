from logging import debug
from typing import List

import csv
import yaml

from schemas import Schema


def deep_update(src: dict, dst: dict):
    """
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    List values will be joined, but not recursed.

    Originally from: https://stackoverflow.com/a/8310229
    """
    for key, value in src.items():
        if key not in dst:
            dst[key] = value
        elif isinstance(value, dict):
            deep_update(value, dst[key])
        elif isinstance(value, list):
            src_list = value
            if len(src_list) > 0:
                dst_list = dst[key]
                dst_list += src_list


def _get_original_key_val(part, key, val=None):
    key_orig = part.get(key + '_original_key')
    val_orig = part.get(key + '_original_val')
    if key_orig:
        key = key_orig
    if val_orig:
        val = val_orig
    elif not val:
        val = part.get(key)
    return (key, val)


def meta_mark(meta, part, key, val=None):
    (key, val) = _get_original_key_val(part, key)
    meta[key] = val
    # print(f'meta marked ({key}, {val})')


def meta_get(meta, part, key):
    """returns `part[key]` and records the retrival in `meta`"""
    val = part.get(key)
    meta_mark(meta, part, key, val)
    return val


def meta_pop(meta, part, key):
    """same as `meta_get` but also removes `key` from `part`."""
    result = meta_get(meta, part, key)
    del part[key]
    return result


# def meta_set(meta, part, key):
#     """returns `part[key]` and records the retrival in `meta`"""


def import_dataset(fileName: str) -> List[dict]:
    """File must be CSV. Returns a list of dicts"""
    result = []
    with open(fileName, newline='') as f:
        for row in csv.DictReader(f):
            result.append(row)
    return result


def import_schema(path: str) -> Schema:
    with open(path, "r") as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def export_schema(schema: Schema, path: str):
    with open(path, "w") as f:
        return f.write(yaml.dump(schema))
