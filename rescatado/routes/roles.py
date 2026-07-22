from flask import Blueprint, jsonify
from extensions import db
from models.roles import Rol

roles_bp = Blueprint('roles', __name__)

@roles_bp.route('/roles', methods=['GET'])
def listar_roles():
    try:
        roles = Rol.query.all()
        resultado = [
            {
                "id_rol": rol.id_rol,
                "nombre_rol": rol.nombre_rol,
                "descripcion": rol.descripcion
            }
            for rol in roles
        ]
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@roles_bp.route('/roles/init', methods=['POST'])
def init_roles():
    try:
        defaults = [
            {"nombre_rol": "Administrador", "descripcion": "Acceso total al sistema"},
            {"nombre_rol": "Operador", "descripcion": "Acceso limitado a despachos y clientes"},
            {"nombre_rol": "Cliente", "descripcion": "Acceso a reservas y seguimiento"}
        ]
        creados = []
        for r in defaults:
            if not Rol.query.filter_by(nombre_rol=r["nombre_rol"]).first():
                nuevo = Rol(nombre_rol=r["nombre_rol"], descripcion=r["descripcion"])
                db.session.add(nuevo)
                creados.append(r["nombre_rol"])
        db.session.commit()
        return {"msg": "Roles iniciales creados", "creados": creados}, 201
    except Exception as e:
        return {"error": str(e)}, 500


