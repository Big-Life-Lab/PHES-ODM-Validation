from typing import List

import csv
import requests

from xlsx2csv import Xlsx2csv


def deep_update(original, update):
    """
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    https://stackoverflow.com/a/8310229
    """
    for key, value in original.items():
        if key not in update:
            update[key] = value
        elif isinstance(value, dict):
            deep_update(value, update[key])
    return update


def convertXlsx2Csv(xlsxFile, sheetName, csvFile: str):
    wb = Xlsx2csv(xlsxFile, outputencoding="utf-8")
    ws = wb.getSheetIdByName(sheetName)
    wb.convert(csvFile, ws)


def importCsvFile(fileName: str) -> List[dict]:
    """Returns a list of dicts"""
    result = []
    with open(fileName, newline='') as f:
        for row in csv.DictReader(f):
            result.append(row)
    return result


def downloadFile(url, dst: str):
    print(f"downloading {dst}...", flush=True)
    r = requests.get(url)
    with open(dst, "wb") as f:
        f.write(r.content)
