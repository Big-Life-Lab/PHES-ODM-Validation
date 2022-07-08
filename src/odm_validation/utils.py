import csv
import requests

# TODO: document requirement
from xlsx2csv import Xlsx2csv


def convertXlsx2Csv(xlsxFile, sheetName, csvFile: str):
    wb = Xlsx2csv(xlsxFile, outputencoding="utf-8")
    ws = wb.getSheetIdByName(sheetName)
    wb.convert(csvFile, ws)


def importCsvFile(fileName: str) -> [dict]:
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
