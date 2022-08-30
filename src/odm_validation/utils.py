from typing import List

import csv


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


def importCsvFile(fileName: str) -> List[dict]:
    """Returns a list of dicts"""
    result = []
    with open(fileName, newline='') as f:
        for row in csv.DictReader(f):
            result.append(row)
    return result
