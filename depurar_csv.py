import csv

def depurar_csv(ruta_csv, salida_csv):
    seen = set()
    with open(ruta_csv, newline='', encoding='utf-8') as infile, \
         open(salida_csv, "w", newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            telefono = row["telefono"].strip()
            if telefono not in seen:
                seen.add(telefono)
                writer.writerow(row)
    print(f"✅ CSV depurado. Guardado en {salida_csv} con {len(seen)} registros únicos.")

if __name__ == "__main__":
    depurar_csv("migracion142025.csv", "clientes_unicos.csv")
