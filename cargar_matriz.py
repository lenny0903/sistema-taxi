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
            # Usamos DictReader para mapear las columnas del CSV
            reader = csv.DictReader(f)
            
            datos = []
            for fila in reader:
                # Mapeamos: El CSV tiene 'combinacion' pero tu tabla tiene 'es_combinacion'
                datos.append((
                    fila['destino'],
                    float(fila['precio_bs']),
                    fila['municipio'],
                    fila['combinacion'] 
                ))

            # El orden debe coincidir con los (?) : destino, precio_bs, municipio, es_combinacion
            cursor.executemany("""
                INSERT INTO matriz_tarifas (destino, precio_bs, municipio, es_combinacion)
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