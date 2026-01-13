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
    # Caducar antes de listar
    caducar_reservas_internamente()

    reservas = Reserva.query.all()
    return jsonify({
        "total": len(reservas),
        "reservas": [reserva.to_dict() for reserva in reservas]
    }), 200

def caducar_reservas_internamente():
    ahora = datetime.now()
    vencidas = Reserva.query.filter(
        Reserva.estado == "activo",
        (Reserva.fecha < ahora.date()) |
        ((Reserva.fecha == ahora.date()) & (Reserva.hora < ahora.time()))
    ).all()
    for r in vencidas:
        r.estado = "inactiva"
    db.session.commit()

import sqlite3
from datetime import datetime

def actualizar_estados_reservas():
    conn = sqlite3.connect('/home/lenny/app_taxis/taxis.db')
    cursor = conn.cursor()

    # Marcar como 'expirada' las reservas que ya vencieron
    cursor.execute("""
        UPDATE reservas
        SET estado = 'expirada'
        WHERE estado = 'activo'
          AND datetime(fecha || ' ' || hora) < datetime('now');
    """)

    # Marcar como 'alerta' las reservas que están dentro de la ventana de despacho (ej. ±15 min)
    cursor.execute("""
        UPDATE reservas
        SET estado = 'alerta'
        WHERE estado = 'activo'
          AND datetime(fecha || ' ' || hora) >= datetime('now')
          AND datetime(fecha || ' ' || hora) <= datetime('now', '+15 minutes');
    """)

    conn.commit()
    conn.close()
    print("🔎 Job ejecutado: estados de reservas actualizados")

from datetime import datetime, timedelta

@reservas_bp.route("/reservas/por_vencer", methods=["GET"])
def listar_reservas_por_vencer():
    ahora = datetime.now()
    limite = ahora + timedelta(minutes=30)

    # 👇 Ejecutar caducación antes de filtrar
    caducar_reservas_internamente()

    reservas = Reserva.query.filter(Reserva.estado == "activo").all()
    resultado = []

    for r in reservas:
        fecha_hora = datetime.combine(r.fecha, r.hora)
        if ahora < fecha_hora <= limite:
            resultado.append(r.to_dict())

    return jsonify({
        "total": len(resultado),
        "reservas": resultado
    }), 200

@reservas_bp.route("/reservas/activas", methods=["GET"])
def listar_reservas_activas():
    caducar_reservas_internamente()
    reservas = Reserva.query.filter_by(estado="activo").all()
    return jsonify({
        "total": len(reservas),
        "reservas": [r.to_dict() for r in reservas]
    }), 200
