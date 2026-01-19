# routes/usuarios.py
import os
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, generate_password_hash
from models.usuarios import Usuario
from models.roles import Rol
from utils.auth_middleware import rol_requerido, token_requerido
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
import os, sqlite3
from utils.db import get_db
from utils.time import hora_local

usuarios_bp = Blueprint('usuarios', __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "taxis.db") 

@usuarios_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id_usuario, u.usuario, u.nombre_completo,
               r.nombre_rol AS nombre_rol, u.activo
        FROM usuarios u
        LEFT JOIN roles r ON u.rol_id = r.id_rol
    """)
    rows = []
    for row in cur.fetchall():
        rows.append({
            "id_usuario": row["id_usuario"],
            "usuario": row["usuario"],
            "nombre_completo": row["nombre_completo"],
            "nombre_rol": row["nombre_rol"] if row["nombre_rol"] else "Sin rol",
            "activo": bool(row["activo"])
        })
    conn.close()
    print("Usuarios encontrados:", rows)
    return jsonify(rows)



@usuarios_bp.route("/usuarios", methods=["POST"])
def crear_usuario():
    data = request.get_json()
    usuario = data.get("usuario")
    nombre = data.get("nombre_completo")
    rol_id = data.get("rol_id")
    clave = data.get("clave")

    if not usuario or not clave or not rol_id or not nombre:
        return jsonify({"error": "Datos incompletos"}), 400

    clave_hash = generate_password_hash(clave)

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO usuarios (usuario, clave_hash, nombre_completo, rol_id, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (usuario, clave_hash, nombre, rol_id))
        conn.commit()
        conn.close()

        return jsonify({"mensaje": "Usuario creado correctamente"}), 201

    except sqlite3.IntegrityError as e:
        # usuario duplicado o constraint violado
        return jsonify({"error": "El usuario ya existe o datos inválidos"}), 409

    except Exception as e:
        import traceback
        print("Error interno:", traceback.format_exc())
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@usuarios_bp.route("/usuarios/<int:id>/estado", methods=["PUT"])
def cambiar_estado_usuario(id):
    data = request.get_json()
    activo = data.get("activo")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET activo = ? WHERE id_usuario = ?", (activo, id))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Estado actualizado"}), 200


# Función auxiliar para obtener conexión
def get_db():
    # Ajusta la ruta según la ubicación real de taxis.db
    db_path = os.path.join(os.path.dirname(__file__), "..", "taxis.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@usuarios_bp.route("/cambiar_password", methods=["PUT"])
def cambiar_password_route():
    data = request.get_json()
    print("Datos recibidos:", data)

    usuario = data.get("usuario")
    password_actual = data.get("password_actual")
    password_nueva = data.get("password_nueva")

    if not usuario or not password_actual or not password_nueva:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    try:
        conn = get_db()
        conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
        cur = conn.cursor()

        cur.execute("SELECT id_usuario, clave_hash, activo FROM usuarios WHERE usuario = ?", (usuario,))
        row = cur.fetchone()
        print("Fila encontrada:", row)

        if not row:
            return jsonify({"error": "Usuario no encontrado"}), 404

        if not row["activo"]:
            return jsonify({"error": "Usuario inactivo"}), 403

        print("Hash en BD:", row["clave_hash"])

        if not check_password_hash(row["clave_hash"], password_actual):
            return jsonify({"error": "Contraseña actual incorrecta"}), 401

        nuevo_hash = generate_password_hash(password_nueva)
        cur.execute("UPDATE usuarios SET clave_hash = ? WHERE id_usuario = ?", (nuevo_hash, row["id_usuario"]))
        conn.commit()
        conn.close()

        return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200

    except Exception as e:
        import traceback
        print("Error interno:", traceback.format_exc())
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@usuarios_bp.route('/perfil', methods=['GET'])
@token_requerido
def ver_perfil():
    identidad = get_jwt_identity()
    usuario = Usuario.query.filter_by(usuario=identidad).first()

    if not usuario:
        return jsonify({'msg': 'Usuario no encontrado'}), 404

    perfil = {
        'usuario': usuario.usuario,
        'nombre_completo': usuario.nombre_completo,
        'rol': usuario.rol.nombre_rol,
        'activo': usuario.activo
    }

    print(f"[BITÁCORA] Acceso a perfil: {usuario.usuario} ({usuario.rol.nombre_rol})")
    return jsonify(perfil), 200

@usuarios_bp.route("/log-acceso", methods=["POST"])
def registrar_log_acceso():
    data = request.get_json()
    usuario = data.get("usuario")
    evento = data.get("evento")
    
    if not usuario or not evento:
        return jsonify({"error": "Datos de auditoría incompletos"}), 400

    try:
        # Obtenemos la hora de Caracas y le quitamos la zona horaria para SQLite
        ahora = hora_local().replace(tzinfo=None)
        
        conn = get_db()
        cur = conn.cursor()
        # Agregamos 'fecha_hora' al INSERT y al VALUES
        cur.execute("""
            INSERT INTO auditoria_accesos (usuario, evento, ip_address, user_agent, fecha_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (
            usuario, 
            evento, 
            request.remote_addr, 
            request.headers.get('User-Agent'),
            ahora  # <--- Enviamos la hora de Caracas aquí
        ))
        conn.commit()
        conn.close()
        return jsonify({"mensaje": "Auditoría registrada"}), 201
    except Exception as e:
        print(f"Error en auditoría: {e}")
        return jsonify({"error": "No se pudo registrar la auditoría"}), 500