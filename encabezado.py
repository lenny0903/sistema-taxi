import csv

with open("migracion142025.csv", newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("Encabezados detectados:", reader.fieldnames)
