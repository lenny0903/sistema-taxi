# utils/auth.py
from functools import wraps
from flask import request, jsonify
import jwt

SECRET_KEY = "clave_secreta_demo"  # cámbiala en producción

def rol_requerido(roles_permitidos):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]

            if not token:
                return jsonify({"msg": "Token requerido"}), 401

            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                if data["rol"] not in roles_permitidos:
                    return jsonify({"msg": "Acceso denegado"}), 403
            except Exception:
                return jsonify({"msg": "Token inválido"}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator
