# routes/usuarios.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models.usuarios import Usuario
from models.roles import Rol
from app import db


usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()

    campos = ['usuario', 'clave', 'nombre_completo', 'rol_id']
    if not all(c in data for c in campos):
        return jsonify({'msg': 'Faltan campos obligatorios'}), 400

    rol = Rol.query.get(data['rol_id'])
    if not rol:
        return jsonify({'msg': 'Rol no válido'}), 400

    if Usuario.query.filter_by(usuario=data['usuario']).first():
        return jsonify({'msg': 'Usuario ya existe'}), 409

    nuevo_usuario = Usuario(
        usuario=data['usuario'],
        clave_hash=generate_password_hash(data['clave']),
        nombre_completo=data['nombre_completo'],
        rol_id=data['rol_id'],
        activo=True
    )

    db.session.add(nuevo_usuario)
    db.session.commit()

    print(f"[BITÁCORA] Usuario creado: {nuevo_usuario.usuario} con rol {rol.nombre_rol}")
    return jsonify({'msg': 'Usuario creado exitosamente'}), 201


from utils.auth_middleware import rol_requerido, token_requerido
from flask_jwt_extended import get_jwt_identity
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