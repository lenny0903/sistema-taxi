import csv
import re
from extensions import db
from models.clientes import Cliente
from app import create_app

def limpiar_valor(v):
    return (v or "").strip()

def normalizar_clave(k):
    k = (k or "").strip().strip('"').strip("'").lower()
    k = re.sub(r'[\s_]+', "_", k)
    return k

def migrar_clientes_csv():
    ruta_csv = "migracion152025.csv"
    with open(ruta_csv, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
        reader.fieldnames = [normalizar_clave(fn) for fn in reader.fieldnames if fn and fn.strip()]

        registros = []
        telefonos_vistos = set()
        descartados = 0

        for row in reader:
            clean_row = {normalizar_clave(k): limpiar_valor(v) for k, v in row.items() if k and k.strip()}

            telefono = clean_row.get("telefono", "")
            nombre = clean_row.get("nombre", "")
            direccion = clean_row.get("direccion", "")
            punto_referencia = clean_row.get("punto_referencia", "")

            if not telefono or telefono in telefonos_vistos:
                descartados += 1
                continue

            telefonos_vistos.add(telefono)

            registros.append(
                Cliente(
                    telefono=telefono,
                    nombre=nombre,
                    direccion=direccion,
                    punto_referencia=punto_referencia
                )
            )

        db.session.bulk_save_objects(registros)
        db.session.commit()
        print(f"✅ Migrados {len(registros)} clientes desde {ruta_csv}")
        print(f"⚠️ {descartados} registros descartados por teléfono vacío o duplicado")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        migrar_clientes_csv()
