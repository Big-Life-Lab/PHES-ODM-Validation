# This is a temporary test file to speed up initial development.

from utils import downloadFile, convertXlsx2Csv, importCsvFile

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
