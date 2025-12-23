import sqlite3
from werkzeug.security import generate_password_hash

# Conexión a la base de datos
db_path = "taxis.db"   # Ajusta si tu archivo tiene otro nombre
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Crear roles únicos
cursor.execute("""
    INSERT OR IGNORE INTO roles (id_rol, nombre_rol)
    VALUES (1, 'Administrador');
""")

cursor.execute("""
    INSERT OR IGNORE INTO roles (id_rol, nombre_rol)
    VALUES (2, 'Operador');
""")

# 2. Generar hashes para las claves
admin_hash = generate_password_hash("1234")   # clave de admin1
operador_hash = generate_password_hash("abcd")  # clave de operador1

# 3. Crear usuario admin1 con rol Administrador
cursor.execute("""
    INSERT OR IGNORE INTO usuarios (usuario, clave_hash, nombre_completo, rol_id, activo)
    VALUES (?, ?, ?, ?, ?);
""", ("admin1", admin_hash, "Administrador del sistema", 1, 1))

# 4. Crear usuario operador1 con rol Operador
cursor.execute("""
    INSERT OR IGNORE INTO usuarios (usuario, clave_hash, nombre_completo, rol_id, activo)
    VALUES (?, ?, ?, ?, ?);
""", ("operador1", operador_hash, "Operador de despacho", 2, 1))

# Guardar cambios y cerrar
conn.commit()
conn.close()

print("✅ Roles y usuarios inicializados: admin1 (1234) y operador1 (abcd).")
