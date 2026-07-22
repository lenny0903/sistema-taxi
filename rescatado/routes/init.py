from flask import Blueprint, jsonify
from extensions import db
from models.roles import Rol
from models.usuarios import Usuario
from models.clientes import Cliente
from models.conductores import Conductor
from models.autos import Auto
from models.despachos import Despacho
from werkzeug.security import generate_password_hash
from datetime import datetime

init_bp = Blueprint('init', __name__)

@init_bp.route('/init', methods=['POST'])
def init_data():
    # =========================
    # ROLES
    # =========================
    if not Rol.query.filter_by(nombre_rol="admin").first():
        db.session.add(Rol(nombre_rol="admin", descripcion="Administrador"))
    if not Rol.query.filter_by(nombre_rol="operador").first():
        db.session.add(Rol(nombre_rol="operador", descripcion="Operador del sistema"))
    db.session.commit()

    # =========================
    # USUARIO ADMIN
    # =========================
    rol_admin = Rol.query.filter_by(nombre_rol="admin").first()
    if not Usuario.query.filter_by(username="admin").first():
        admin = Usuario(
            username="admin",
            password_hash=generate_password_hash("1234"),
            nombre_completo="Administrador General",
            rol_id=rol_admin.id_rol,
            activo=True
        )
        db.session.add(admin)
        db.session.commit()

    # =========================
    # CLIENTE DEMO
    # =========================
    if not Cliente.query.filter_by(telefono="04141234567").first():
        cliente = Cliente(
            telefono="04141234567",
            nombre="Cliente Demo",
            direccion="Av. Principal #123"
        )
        db.session.add(cliente)
        db.session.commit()

    # =========================
    # CONDUCTOR DEMO
    # =========================
    if not Conductor.query.filter_by(cod_conductor="C001").first():
        conductor = Conductor(
            cod_conductor="C001",
            nombre="Conductor Demo",
            nro_telefono="04149876543"
        )
        db.session.add(conductor)
        db.session.commit()

    # =========================
    # AUTO DEMO
    # =========================
    if not Auto.query.filter_by(nro_placa="ABC123").first():
        auto = Auto(
            nro_placa="ABC123",
            tipo_auto="Sedán",
            marca="Toyota",
            modelo="Corolla"
        )
        db.session.add(auto)
        db.session.commit()

    # =========================
    # DESPACHO DEMO
    # =========================
    cliente = Cliente.query.filter_by(telefono="04141234567").first()
    conductor = Conductor.query.filter_by(cod_conductor="C001").first()
    auto = Auto.query.filter_by(nro_placa="ABC123").first()

    if not Despacho.query.filter_by(cliente_id=cliente.id_cliente).first():
        despacho = Despacho(
            fecha_hora_inicio=datetime.now(),
            origen_despacho="Terminal",
            destino_despacho="Centro",
            cliente_id=cliente.id_cliente,
            conductor_id=conductor.id_conductor,
            auto_id=auto.id_auto,
            tarifa=10.0,
            estado_despacho="en curso"
        )
        db.session.add(despacho)
        db.session.commit()

    return jsonify({"msg": "Datos iniciales creados"}), 201
