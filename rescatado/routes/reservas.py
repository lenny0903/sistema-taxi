from flask import Blueprint, request, jsonify
from extensions import db
from models.reserva import Reserva
from models.clientes import Cliente
from datetime import datetime


reservas_bp = Blueprint("reservas", __name__)

@reservas_bp.route("/reservas", methods=["POST"])
def crear_reserva():
    data = request.get_json()

    # Validar que venga cliente_id
    cliente_id = data.get("cliente_id")
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    try:
        nueva_reserva = Reserva(
            origen=data["origen"],
            destino=data["destino"],
            fecha=datetime.strptime(data["fecha"], "%Y-%m-%d").date(),
            hora=datetime.strptime(data["hora"], "%H:%M").time(),
            cliente_id=cliente_id
        )

        db.session.add(nueva_reserva)
        db.session.commit()

        return jsonify({
            "message": "Reserva creada exitosamente",
            "reserva": nueva_reserva.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@reservas_bp.route("/clientes/<int:cliente_id>/reservas", methods=["GET"])
def listar_reservas_por_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    reservas = Reserva.query.filter_by(cliente_id=cliente_id).all()
    return jsonify({
        "cliente": cliente.to_dict(),
        "reservas": [reserva.to_dict() for reserva in reservas]
    }), 200

@reservas_bp.route("/reservas", methods=["GET"])
def listar_reservas():
    reservas = Reserva.query.all()
    return jsonify({
        "total": len(reservas),
        "reservas": [reserva.to_dict() for reserva in reservas]
    }), 200
