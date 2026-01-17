import sqlite3

def emparejar_todo():
    conn = sqlite3.connect("taxis.db")
    cursor = conn.cursor()

    # Esta consulta busca el auto correcto basado en el código del conductor 
    # y lo actualiza tanto en turnos como en despachos.
    queries = [
        # Actualizar Turnos
        """
        UPDATE turnos
        SET id_auto = (
            SELECT a.id_auto 
            FROM autos a 
            JOIN conductores c ON a.nro_placa LIKE '%' || c.codigo || '%'
            WHERE c.id_conductor = turnos.id_conductor
            LIMIT 1
        )
        """,
        # Actualizar Despachos
        """
        UPDATE despachos
        SET id_auto = (
            SELECT a.id_auto 
            FROM autos a 
            JOIN conductores c ON a.nro_placa LIKE '%' || c.codigo || '%'
            WHERE c.id_conductor = despachos.id_conductor
            LIMIT 1
        )
        """
    ]

    try:
        for q in queries:
            cursor.execute(q)
            print(f"✅ Registros actualizados: {cursor.rowcount}")
        
        conn.commit()
        print("\n🚀 Sincronización completa. Ahora el historial es coherente.")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

emparejar_todo()