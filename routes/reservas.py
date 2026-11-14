from flask import Blueprint, render_template, request, jsonify
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

@reservas_bp.route("/clientes/telefono/<telefono>", methods=["GET"])
def obtener_cliente_por_telefono(telefono):
    # Asumiendo que tu modelo Cliente tiene los campos telefono, nombre, direccion, etc.
    cliente = Cliente.query.filter_by(telefono=telefono).first()
    if cliente:
        return jsonify({
            "existe": True,
            "id_cliente": cliente.id_cliente, # Ajusta al nombre real de tu PK (id o id_cliente)
            "nombre": cliente.nombre,
            "direccion": cliente.direccion
        }), 200
    return jsonify({"existe": False}), 200

@reservas_bp.route("/clientes", methods=["POST"])
def crear_cliente():
    data = request.get_json()
    telefono = data.get("telefono")
    nombre = data.get("nombre")
    direccion = data.get("direccion")

    if not telefono or not nombre:
        return jsonify({"error": "Teléfono y nombre son obligatorios"}), 400

    try:
        nuevo_cliente = Cliente(
            telefono=telefono,
            nombre=nombre,
            direccion=direccion
        )
        db.session.add(nuevo_cliente)
        db.session.commit()

        return jsonify({
            "message": "Cliente registrado exitosamente",
            "id_cliente": nuevo_cliente.id_cliente # Ajusta según tu modelo
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@reservas_bp.route("/reservas/crear_desde_web", methods=["POST"])
def crear_reserva_desde_web():
    # 1. Capturar datos ya sea por Formulario Web (HTML) o JSON (API)
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    telefono = data.get("telefono") or data.get("desTelefono")
    nombre = data.get("nombre") or data.get("desNombre", "Cliente Web")
    origen = data.get("origen") or data.get("nuevo_origen") or data.get("desOrigen")
    destino = data.get("destino") or data.get("destino_1")
    
    # Manejo de fecha y hora para reservas
    fecha_str = data.get("fecha_reserva") or data.get("fecha")
    hora_str = data.get("hora_reserva") or data.get("hora")
    tipo_solicitud = data.get("tipo_solicitud", "inmediato")

    if not telefono or not origen:
        return jsonify({"error" : "Teléfono y origen son obligatorios"}), 400

    try:
        # 2. Buscar o crear el cliente automáticamente utilizando el teléfono (igual que el operador)
        cliente = Cliente.query.filter_by(telefono=telefono).first()
        if not cliente:
            cliente = Cliente(
                telefono=telefono,
                nombre=nombre,
                direccion=origen
            )
            db.session.add(cliente)
            db.session.commit()

       # 3. Validar si es una reserva programada o un despacho inmediato
        if tipo_solicitud == "reserva" and fecha_str and hora_str:
            nueva_reserva = Reserva(
                origen=origen,
                destino=destino or "A convenir",
                fecha=datetime.strptime(fecha_str, "%Y-%m-%d").date(),
                hora=datetime.strptime(hora_str, "%H:%M").time(),
                cliente_id=cliente.id_cliente,
                estado="activo"
            )
            db.session.add(nueva_reserva)
            db.session.commit()
            
            return render_template('reserva_exitosa.html', id_reserva=nueva_reserva.id_reserva), 200
        else:
            # 🚕 Si es inmediato, puedes registrarlo como despacho/turno o mostrar una vista similar de éxito
            # (Por ahora, puedes renderizar la misma plantilla o una adaptada para servicios inmediatos)
            return render_template('reserva_exitosa.html', id_reserva="Inmediato"), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400     