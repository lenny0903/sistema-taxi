from flask import Blueprint, request, jsonify
from extensions import db
from models import ColaDespacho, Cliente
from datetime import datetime
from flask import current_app 

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



@cola_despachos_bp.route("/webhook_wa", methods=["POST"])
def webhook_wa():
    try:
        data = request.get_json(force=True)
        telefono = data.get("telefono")
        mensaje = data.get("mensaje") # El texto que el cliente escribió
        nombre_wa = data.get("nombre", "Cliente WhatsApp")

        if not telefono:
            return jsonify({"error": "Teléfono es obligatorio"}), 400

        # 1. Buscar o crear cliente (Misma lógica que ya tienes)
        cliente = Cliente.query.filter_by(telefono=telefono).first()
        if not cliente:
            cliente = Cliente(
                nombre=nombre_wa,
                telefono=telefono,
                direccion=mensaje # Usamos el primer mensaje como dirección base
            )
            db.session.add(cliente)
            db.session.commit()

        # 2. Determinar el origen (Regla 2026-01-13)
        # Si el cliente escribió algo, ese es su origen hoy. 
        # Si mandó un mensaje vacío (solo un hola), traemos su dirección de la base de datos.
        origen_final = mensaje if (mensaje and len(mensaje) > 3) else cliente.direccion

        # 3. Crear entrada en la cola
        nueva_cola = ColaDespacho(
            id_cliente=cliente.id_cliente,
            origen=origen_final,
            destino="", # El operador lo llenará en el modal
            estado="En espera",
            fecha_creacion=datetime.utcnow()
        )
        
        db.session.add(nueva_cola)
        db.session.commit()

        # 4. 🔥 NOTIFICACIÓN EN TIEMPO REAL
        # Esto le avisa a tu front-end que debe ejecutar cargarColaClientes()
        if 'socketio' in current_app.extensions:
            socketio = current_app.extensions['socketio']
            socketio.emit('cola_actualizada', {'msj': 'Nuevo pedido de WA'}, namespace='/')

        return jsonify({"status": "success", "id": nueva_cola.id_cola}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en Webhook WA: {e}")
        return jsonify({"error": str(e)}), 500    