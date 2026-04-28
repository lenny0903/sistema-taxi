import sqlite3

def buscar_tarifa():
    # Conectamos a la base de datos
    try:
        conn = sqlite3.connect('taxis.db')
        cursor = conn.cursor()

        print("--- 🚖 CONSULTA DE TARIFAS LOS PATRIOTAS ---")
        destino_buscado = input("Escriba el destino (ej: Rubio, Arjona, Pirineos): ").strip()

        # Buscamos usando LIKE para que encuentre coincidencias parciales
        # Usamos UPPER para que no importe si escribe en mayúsculas o minúsculas
        query = """
            SELECT destino, precio_cop, municipio 
            FROM matriz_tarifas 
            WHERE destino LIKE ? 
            LIMIT 5
        """
        cursor.execute(query, (f'%{destino_buscado}%',))
        resultados = cursor.fetchall()

        if resultados:
            print(f"\n✅ Se encontraron {len(resultados)} coincidencia(s):")
            print("-" * 45)
            for res in resultados:
                destino, precio, municipio = res
                
                # FORMATEO DE MILES: Convertimos 70000 en 70.000
                precio_formateado = "{:,.0f}".format(precio).replace(",", ".")
                
                print(f"📍 DESTINO: {destino}")
                print(f"🏢 MUNICIPIO: {municipio}")
                print(f"💰 TARIFA: {precio_formateado} COP")
                print("-" * 45)
        else:
            print(f"\n❌ No se encontró ningún destino que coincida con '{destino_buscado}'")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    buscar_tarifa()