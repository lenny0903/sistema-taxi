from flask import Blueprint, request, jsonify
from extensions import db
from models import ColaDespacho, Cliente
from datetime import datetime
from flask import current_app 

cola_despachos_bp = Blueprint("cola_despachos", __name__)

@cola_despachos_bp.route("/", methods=["GET", "POST"])
def cola_despachos():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            telefono = data.get("telefono")
            nombre = data.get("nombre")
            origen_actual = data.get("origen")
            destino_actual = data.get("destino")
            
            # 🔹 Capturamos la tarifa recibida en el POST (default 0 si no viene)
            raw_tarifa = data.get("tarifa")
            try:
                tarifa_actual = float(raw_tarifa) if raw_tarifa not in [None, ""] else 0
            except (ValueError, TypeError):
                tarifa_actual = 0

            if not telefono or not origen_actual:
                return jsonify({"error": "Teléfono y origen son obligatorios"}), 400

            # Buscar o crear cliente
            cliente = Cliente.query.filter_by(telefono=telefono).first()
            if not cliente:
                cliente = Cliente(
                    nombre=nombre,
                    telefono=telefono,
                    direccion=origen_actual
                )
                db.session.add(cliente)
                db.session.commit()

            # Crear entrada en la cola registrando la tarifa y guardando en BD (Persistente)
            cola = ColaDespacho(
                id_cliente=cliente.id_cliente,
                origen=origen_actual,   
                destino=destino_actual,
                tarifa=tarifa_actual,
                estado="En espera",
                fecha_creacion=datetime.utcnow()
            )
            
            db.session.add(cola)
            db.session.commit()

            return jsonify(cola.to_dict()), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear en la cola: {e}")
            return jsonify({"error": str(e)}), 500

    elif request.method == "GET":
        try:
            # Consultamos directamente a la base de datos SQLite con seguridad ante errores
            colas = ColaDespacho.query.order_by(ColaDespacho.fecha_creacion.asc()).all()
            return jsonify([c.to_dict() for c in colas]), 200
        except Exception as e:
            print(f"❌ Error al leer la cola: {e}")
            return jsonify([]), 200
    
@cola_despachos_bp.route("/<int:id>", methods=["DELETE"])
def cancelar_cola(id):
    try:
        cola = ColaDespacho.query.get(id)
        if not cola:
            return jsonify({"error": "Cliente no encontrado en cola"}), 404

        db.session.delete(cola)
        db.session.commit()
        return jsonify({"msg": "Cliente cancelado", "id": id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cola_despachos_bp.route("/webhook_wa", methods=["POST"])
def webhook_wa():
    try:
        data = request.get_json(force=True)
        telefono = data.get("telefono")
        mensaje = data.get("mensaje") # El texto que el cliente escribió
        nombre_wa = data.get("nombre", "Cliente WhatsApp")

        if not telefono:
            return jsonify({"error": "Teléfono es obligatorio"}), 400

        # 1. Buscar o crear cliente
        cliente = Cliente.query.filter_by(telefono=telefono).first()
        if not cliente:
            cliente = Cliente(
                nombre=nombre_wa,
                telefono=telefono,
                direccion=mensaje if mensaje else "Sin dirección"
            )
            db.session.add(cliente)
            db.session.commit()

        # 2. Determinar el origen (Regla base de datos / mensaje)
        origen_final = mensaje if (mensaje and len(mensaje) > 3) else cliente.direccion

        # 3. Crear entrada persistente en la cola
        nueva_cola = ColaDespacho(
            id_cliente=cliente.id_cliente,
            origen=origen_final,
            destino="", # El operador lo llenará en el panel
            estado="En espera",
            fecha_creacion=datetime.utcnow()
        )
        
        db.session.add(nueva_cola)
        db.session.commit()

        # 4. 🔥 NOTIFICACIÓN EN TIEMPO REAL
        if 'socketio' in current_app.extensions:
            socketio = current_app.extensions['socketio']
            socketio.emit('cola_actualizada', {'msj': 'Nuevo pedido de WA'}, namespace='/')

        return jsonify({"status": "success", "id": nueva_cola.id_cola}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en Webhook WA: {e}")
        return jsonify({"error": str(e)}), 500