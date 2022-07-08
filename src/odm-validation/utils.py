import csv
import requests

# TODO: document requirement
from xlsx2csv import Xlsx2csv


def convertXlsx2Csv(xlsxFile, sheetName, csvFile: str):
    wb = Xlsx2csv(xlsxFile, outputencoding="utf-8")
    ws = wb.getSheetIdByName(sheetName)
    wb.convert(csvFile, ws)


def importCsvFile(fileName: str) -> (dict, list):
    """Return (cols, rows)"""
    cols = {}
    rows = []
    with open(fileName, newline='') as f:
        r = csv.reader(f)
        headers = next(r)
        cols = dict(zip(headers, range(len(headers))))
        for row in r:
            rows.append(row)
    return (cols, rows)


def downloadFile(url, dst: str):
    print(f"downloading {dst}...", flush=True)
    r = requests.get(url)
    with open(dst, "wb") as f:
        f.write(r.content)


xlsxSchemaSheet = "parts"
xlsxSchema = "schema.xlsx"
csvSchema = "schema.csv"
xlsxSchemaUrl = "https://osf.io/download/k94qe/"

downloadFile(xlsxSchemaUrl, xlsxSchema)
convertXlsx2Csv(xlsxSchema, xlsxSchemaSheet, csvSchema)
(cols, rows) = importCsvFile(csvSchema)

partId = cols["partID"]
for row in rows:
    print(row[partId])
