import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import jwt
from models.usuarios import Usuario
from models.roles import Rol
from werkzeug.security import check_password_hash   
from utils.hashing import verificar_clave
from functools import wraps
from app import db
from flask import Blueprint, request, jsonify

#bp = Blueprint('auth', __name__, url_prefix='/auth')
from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
SECRET_KEY = "clave_secreta_demo"  # cámbiala en producción

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = Usuario.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # Token con claims adicionales
        access_token = create_access_token(
            identity=str(user.id_usuario),
            additional_claims={
                "rol_id": user.rol_id,
                "rol_nombre": user.rol.nombre_rol,
                "rol_descripcion": user.rol.descripcion
            }
        )

        return jsonify({
            "access_token": access_token,
            "user_id": user.id_usuario,
            "username": user.username,
            "rol_id": user.rol_id,
            "rol_nombre": user.rol.nombre_rol,
            "rol_descripcion": user.rol.descripcion
        }), 200
    else:
        return jsonify({"msg": "Credenciales inválidas"}), 401


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
            except Exception as e:
                return jsonify({"msg": "Token inválido"}), 401

            return f(*args, **kwargs)
        return wrapper
    return decorator

@auth_bp.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()

    # Validar datos mínimos
    if not data.get("username") or not data.get("password") or not data.get("rol_id"):
        return jsonify({"msg": "Faltan datos obligatorios"}), 400

    # Verificar si el usuario ya existe
    if Usuario.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Usuario ya existe"}), 400

    # Buscar rol por id
    rol = Rol.query.get(data["rol_id"])
    if not rol:
        return jsonify({"msg": "Rol inválido"}), 400

    # Crear usuario
    nuevo_usuario = Usuario(
        username=data["username"],
        nombre_completo=data.get("nombre_completo", data["username"]),
        rol_id=rol.id_rol
    )
    nuevo_usuario.set_password(data["password"])
    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({
        "msg": "Usuario creado exitosamente",
        "id_usuario": nuevo_usuario.id_usuario,
        "username": nuevo_usuario.username,
        "rol_id": rol.id_rol
    }), 201


from flask import render_template, redirect, url_for

@auth_bp.route("/login_html", methods=["POST"])
def login_html():
    username = request.form.get("username")
    password = request.form.get("password")

    user = Usuario.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # 🔑 Redirige al dashboard SPA
        return redirect(url_for("panel_html"))
    else:
        return render_template("index.html", error="Credenciales inválidas")
