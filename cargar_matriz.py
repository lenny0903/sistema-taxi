import sqlite3
import csv
import os

def cargar_datos():
    nombre_db = 'taxis.db'
    nombre_csv = 'matriz_cobro_los_patriotas.csv'
    
    if not os.path.exists(nombre_csv):
        print(f"❌ Error: No se encuentra el archivo {nombre_csv}")
        return

    try:
        conn = sqlite3.connect(nombre_db)
        cursor = conn.cursor()

        # Limpiamos la tabla para evitar duplicados en el MVP
        cursor.execute("DELETE FROM matriz_tarifas")
        
        with open(nombre_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            datos = []
            for fila in reader:
                # Obtenemos el precio (sea que en el CSV se llame 'precio_bs' o 'precio_cop')
                precio_val = fila.get('precio_cop') or fila.get('precio_bs') or 0
                
                datos.append((
                    fila['destino'],
                    float(precio_val),
                    fila['municipio'],
                    fila.get('combinacion', 'no') 
                ))

            # 📌 Insertamos en la columna precio_cop
            cursor.executemany("""
                INSERT INTO matriz_tarifas (destino, precio_cop, municipio, es_combinacion)
                VALUES (?, ?, ?, ?)
            """, datos)

        conn.commit()
        print(f"✅ ¡Éxito! Se cargaron {len(datos)} registros en la tabla matriz_tarifas.")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    cargar_datos()