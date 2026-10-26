from flask import Blueprint, request, jsonify
from extensions import db
from models import ColaDespacho, Cliente
from datetime import datetime, timedelta
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

            # 🛡️ PROTECCIÓN ANTI-DUPLICADOS RECIENTE (Evita doble registro en menos de 5 segundos)
            limite_tiempo = datetime.utcnow() - timedelta(seconds=5)
            duplicado_reciente = ColaDespacho.query.filter_by(
                id_cliente=cliente.id_cliente,
                origen=origen_actual,
                estado="En espera"
            ).filter(ColaDespacho.fecha_creacion >= limite_tiempo).first()

            if duplicado_reciente:
                return jsonify({"error": "Este despacho ya fue registrado hace un instante."}), 400

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
            # Consultamos directamente a la base de datos con seguridad ante errores
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

        # 🛡️ Opcional: Protección anti-duplicados también para WhatsApp
        limite_tiempo = datetime.utcnow() - timedelta(seconds=5)
        duplicado_wa = ColaDespacho.query.filter_by(
            id_cliente=cliente.id_cliente,
            origen=origen_final,
            estado="En espera"
        ).filter(ColaDespacho.fecha_creacion >= limite_tiempo).first()

        if duplicado_wa:
            return jsonify({"status": "error", "message": "Mensaje duplicado de WhatsApp reciente"}), 400

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

@cola_despachos_bp.route('/lote', methods=['POST'])
def registrar_lote_despachos():
    datos = request.json.get('despachos', [])

    if not datos:
        return jsonify({"error": "No hay datos para procesar"}), 400

    try:
        for item in datos:
            nuevo_lote = ColaDespacho(
                id_cliente=item.get('cliente_id'),
                origen=item.get('origen'),
                destino=item.get('destino', ''),
                tarifa=item.get('tarifa', 0),
                estado=item.get('estado', 'En espera'),
                fecha_creacion=datetime.utcnow()
            )
            db.session.add(nuevo_lote)
        
        db.session.commit() # ✔ Guardado masivo con SQLAlchemy de forma segura
        return jsonify({"status": "success", "message": f"Lote de {len(datos)} unidades procesado"}), 201

    except Exception as e:
        db.session.rollback() # 🔄 Reversión total si ocurre un fallo
        return jsonify({"error": "Fallo en la transacción: " + str(e)}), 500