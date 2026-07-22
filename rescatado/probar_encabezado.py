import csv

def limpiar_valor(v):
    return (v or "").strip()

def normalizar_clave(k):
    return (k or "").strip().lower().replace(" ", "_")

ruta_csv = "migracion152025.csv"

with open(ruta_csv, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')

    # Normalizar encabezados
    reader.fieldnames = [normalizar_clave(fn) for fn in reader.fieldnames if fn and fn.strip()]

    print("Encabezados normalizados:", reader.fieldnames)

    # Mostrar primeros 5 registros ya limpios
    for i, row in enumerate(reader):
        clean_row = {normalizar_clave(k): limpiar_valor(v) for k, v in row.items() if k and k.strip()}

        telefono = clean_row.get("telefono", "")
        nombre = clean_row.get("nombre", "")
        direccion = clean_row.get("direccion", "")
        punto_referencia = clean_row.get("punto_referencia", "")

        print(f"Fila {i+1}: Tel={telefono}, Nombre={nombre}, Dir={direccion}, Ref={punto_referencia}")

        if i == 4:
            break
