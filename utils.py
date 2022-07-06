import csv

# TODO: document requirement
from xlsx2csv import Xlsx2csv

# TODO: dynamic input filename
csvFile = "data.csv"
excelFile = "data.xlsx"

# convert excel to csv
wb = Xlsx2csv(excelFile, outputencoding="utf-8")
ws = wb.getSheetIdByName("parts")
wb.convert(csvFile, ws)

# import csv
cols = {}
rows = []
with open(csvFile, newline='') as f:
    r = csv.reader(f)
    headers = next(r)
    cols = dict(zip(headers, range(len(headers))))
    for row in r:
        rows.append(row)

partId = cols["partID"]
for row in rows:
    print(row[partId])
