from flask import Blueprint, request, jsonify
from extensions import db
from models import ColaDespacho, Cliente
from datetime import datetime

cola_despachos_bp = Blueprint("cola_despachos", __name__)

@cola_despachos_bp.route("/", methods=["GET", "POST"])
def cola_despachos():
    if request.method == "POST":
        data = request.get_json(force=True)
        telefono = data.get("telefono")
        nombre = data.get("nombre")
        origen_actual = data.get("origen")
        destino_actual = data.get("destino") # 🔹 Capturamos destino

        if not telefono or not origen_actual:
            return jsonify({"error": "Teléfono y origen son obligatorios"}), 400

        # Buscar o crear cliente
        cliente = Cliente.query.filter_by(telefono=telefono).first()
        if not cliente:
            # Si el cliente es nuevo, lo creamos con la dirección actual como base
            cliente = Cliente(
                nombre=nombre,
                telefono=telefono,
                direccion=origen_actual
            )
            db.session.add(cliente)
            db.session.commit()

        # Crear entrada en la cola
        # 🔹 Guardamos origen y destino específicos de ESTA llamada
        cola = ColaDespacho(
            id_cliente=cliente.id_cliente,
            origen=origen_actual,   
            destino=destino_actual,
            estado="En espera",
            fecha_creacion=datetime.utcnow()
        )
        
        db.session.add(cola)
        db.session.commit()

        return jsonify(cola.to_dict()), 201

    elif request.method == "GET":
        # Ordenamos por fecha para que el primero en llamar sea el primero en la lista
        colas = ColaDespacho.query.order_by(ColaDespacho.fecha_creacion.asc()).all()
        return jsonify([c.to_dict() for c in colas]), 200

@cola_despachos_bp.route("/<int:id>", methods=["DELETE"])
def cancelar_cola(id):
    cola = ColaDespacho.query.get(id)
    if not cola:
        return jsonify({"error": "Cliente no encontrado en cola"}), 404

    db.session.delete(cola)
    db.session.commit()
    return jsonify({"msg": "Cliente cancelado", "id": id}), 200

@cola_despachos_bp.route("/", methods=["GET"])
def listar_cola():
    try:
        # Usamos try/except dentro de la consulta por si hay datos corruptos
        colas = ColaDespacho.query.order_by(ColaDespacho.fecha_creacion.asc()).all()
        return jsonify([c.to_dict() for c in colas]), 200
    except Exception as e:
        print(f"❌ Error al leer la cola: {e}")
        # Si falla por las fechas, devolvemos una lista vacía para que la app no muera
        return jsonify([]), 200