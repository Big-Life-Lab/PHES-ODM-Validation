import csv

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


sheetName = "parts"
xlsxFile = "data.xlsx"
csvFile = "data.csv"

convertXlsx2Csv(xlsxFile, sheetName, csvFile)
(cols, rows) = importCsvFile(csvFile)

partId = cols["partID"]
for row in rows:
    print(row[partId])
