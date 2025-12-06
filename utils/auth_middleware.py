from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from models.usuarios import Usuario

def rol_requerido(roles_permitidos):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            identidad = get_jwt_identity()
            usuario = Usuario.query.filter_by(usuario=identidad).first()

            if not usuario or not usuario.activo:
                return jsonify({'msg': 'Usuario no válido o inactivo'}), 403

            nombre_rol = usuario.rol.nombre_rol
            if nombre_rol not in roles_permitidos:
                return jsonify({'msg': f'Acceso denegado para el rol: {nombre_rol}'}), 403

            return func(*args, **kwargs)
        return wrapper
    return decorador

def token_requerido(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        identidad = get_jwt_identity()
        usuario = Usuario.query.filter_by(usuario=identidad).first()

        if not usuario or not usuario.activo:
            return jsonify({'msg': 'Usuario no válido o inactivo'}), 403

        return fn(*args, **kwargs)
    return wrapper