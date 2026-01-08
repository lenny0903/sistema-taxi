from flask import Blueprint, app, request, jsonify, abort
from extensions import db
from models import ColaDespacho, Cliente
from datetime import datetime

cola_despachos_bp = Blueprint("cola_despachos", __name__)

# 👉 Crear nuevo despacho en cola (POST) y listar todos (GET)
@cola_despachos_bp.route("/", methods=["GET", "POST"])
def cola_despachos():
    if request.method == "POST":
        data = request.get_json(force=True)  # fuerza parseo JSON
        telefono = data.get("telefono")
        nombre = data.get("nombre")
        origen = data.get("origen")
        nro_autos = data.get("nro_autos", 1)

        # Buscar o crear cliente
        cliente = Cliente.query.filter_by(telefono=telefono).first()
        if not cliente:
            cliente = Cliente(
                nombre=nombre,
                telefono=telefono,
                direccion=origen
            )
            db.session.add(cliente)
            db.session.commit()

        # Crear cola
        cola = ColaDespacho(
            id_cliente=cliente.id_cliente,
            nro_autos=nro_autos,
            estado="En espera",
            fecha_creacion=datetime.utcnow()
        )
        db.session.add(cola)
        db.session.commit()

        return jsonify(cola.to_dict()), 201

    elif request.method == "GET":
        colas = ColaDespacho.query.order_by(ColaDespacho.fecha_creacion.desc()).all()
        return jsonify([c.to_dict() for c in colas]), 200

@cola_despachos_bp.route("/<int:id>", methods=["DELETE"])
def cancelar_cola(id):
    # Buscar la cola en la base de datos
    cola = ColaDespacho.query.get(id)
    if not cola:
        return jsonify({"error": "Cliente no encontrado en cola"}), 404

    # Eliminar la cola
    db.session.delete(cola)
    db.session.commit()

    return jsonify({"msg": "Cliente cancelado", "id": id}), 200