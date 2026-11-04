from flask import Blueprint, app, request, jsonify
from extensions import db
from models import ColaDespacho, Cliente
from datetime import datetime, timedelta
from flask import current_app 
from extensions import db, socketio

cola_despachos_bp = Blueprint("cola_despachos", __name__)
solicitudes_bp = Blueprint("solicitudes", __name__)
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def obtener_serializer():
    """Crea el serializer dentro del contexto de la app"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
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
            # Consultamos directamente a la base de datos SQLite con seguridad ante errores[cite: 3]
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

        # 🛡️ Protección anti-duplicados también para WhatsApp[cite: 2]
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
        
        db.session.commit() # ✔ Guardado masivo con SQLAlchemy de forma segura[cite: 2]
        return jsonify({"status": "success", "message": f"Lote de {len(datos)} unidades procesado"}), 201

    except Exception as e:
        db.session.rollback() # 🔄 Reversión total si ocurre un fallo[cite: 2]
        return jsonify({"error": "Fallo en la transacción: " + str(e)}), 500

from itsdangerous import URLSafeTimedSerializer
from flask import request, jsonify, render_template, current_app
from routes.incidencias import verificar_veto_cliente



# ============================================================
# RUTA 1: Generar token (llamada desde el pre-banner)
# ============================================================
@solicitudes_bp.route('/api/generar_link_solicitud', methods=['POST'])
def generar_link_solicitud():
    serializer = obtener_serializer()  # 👈 Se crea aquí
    data = request.get_json()
    telefono = data.get('telefono')
    
    if not telefono:
        return jsonify({"error": "Teléfono requerido"}), 400
    
    token = serializer.dumps({"telefono": telefono}, salt="solicitud-cola")
    return jsonify({"token": token})


# ============================================================
# RUTA 2: Mostrar formulario al cliente (GET)
# ============================================================
# Asegúrate de importar el modelo arriba del archivo:
from models.matriz_tarifas import MatrizTarifa

@solicitudes_bp.route('/solicitar/<token>')
def formulario_solicitud(token):
    from flask import current_app
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        # Aumentamos a 24 horas (86400) para que no te moleste en las pruebas
        data = serializer.loads(token, salt="solicitud-cola", max_age=86400) 
    except Exception as e:
        import traceback
        print("❌ ERROR REAL DEL TOKEN:", traceback.format_exc()) # Lo verás en la terminal
        return f"Error al validar token: {str(e)}", 410
    
    telefono = data['telefono']
    cliente = Cliente.query.filter_by(telefono=telefono).first()
    
    # 🚀 AQUÍ CONSULTAMOS LAS TARIFAS REALES DE TU BASE DE DATOS
    tarifas_db = MatrizTarifa.query.all()
    
    # Las formateamos como una lista de diccionarios para que JavaScript las entienda
    lista_tarifas = [
        {
            "destino": t.destino,
            "precio": t.precio_cop
        } 
        for t in tarifas_db
    ]
    
    return render_template(
        'formulario_solicitud.html', 
        telefono=telefono, 
        nombre=cliente.nombre if cliente else "",
        direccion=cliente.direccion if cliente else "",
        tarifas=lista_tarifas, # 👈 ¡AQUÍ LE PASAMOS LA LISTA AL HTML!
        token=token
    )


# ============================================================
# RUTA 3: Procesar formulario y LLENAR LA COLA (POST)
# ============================================================
@solicitudes_bp.route('/solicitar/<token>', methods=['POST'])
def procesar_solicitud(token):
    serializer = obtener_serializer()  # 👈 Se crea aquí
    from flask import current_app
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        data = serializer.loads(token, salt="solicitud-cola", max_age=86400)
    except Exception as e:
        return f"Error al validar token: {str(e)}", 410
    # 🚨 ESTO NOS DIRÁ EXACTAMENTE QUÉ ESTÁ LLEGANDO
    print("\n=== DATOS RECIBIDOS DEL FORMULARIO ===")
    print(request.form.to_dict())
    print("======================================\n")
    
    telefono = data['telefono']
    nombre = request.form.get('nombre', '').strip()
    
    # 🚀 NUEVA LÓGICA PARA RESOLVER EL ORIGEN
    es_misma = request.form.get('es_misma_direccion', 'SI')
    origen_escrito = request.form.get('nuevo_origen', '').strip()
    
    cliente = Cliente.query.filter_by(telefono=telefono).first()
    
    if es_misma == 'NO':
        origen = origen_escrito
    else:
        origen = cliente.direccion if cliente else ""
        if not origen:
            origen = origen_escrito

    # 🚀 LÓGICA PARA RESOLVER LOS DESTINOS (por si el cliente pide varios)
    cantidad = int(request.form.get('cantidad_autos', 1))
    mismo_destino = request.form.get('mismo_destino', 'SI')
    
    destinos = []
    if cantidad == 1 or mismo_destino == 'SI':
        dest_unico = request.form.get('destino_1', '').strip()
        destinos = [dest_unico] * cantidad
    else:
        for i in range(1, cantidad + 1):
            destinos.append(request.form.get(f'destino_{i}', '').strip())

    # 🚨 VALIDACIÓN ESTRICTA
    if not origen:
        return render_template(
            'solicitud_recibida.html',
            mensaje="El origen es obligatorio. Regrese y complete el formulario.",
            exito=False
        ), 400
    
    # Buscar o crear cliente
    if not cliente:
        cliente = Cliente(
            telefono=telefono,
            nombre=nombre or "Cliente",
            direccion=origen
        )
        db.session.add(cliente)
        db.session.commit()
    
    # 🛑 Validación silenciosa de veto
    requiere_revision = False
    try:
        veto = verificar_veto_cliente(cliente.id_cliente)  # Tu función existente
        requiere_revision = veto.get("tiene_veto_general", False)
    except Exception as e:
        print(f"⚠️ Error verificando veto (silencioso): {e}")
        requiere_revision = False
    
    # 🚨 VERIFICAR DUPLICADOS (evitar doble envío)
    entrada_existente = ColaDespacho.query.filter_by(
        id_cliente=cliente.id_cliente,
        estado="En espera"  
    ).first()
    
    if entrada_existente:
        return render_template(
            'solicitud_recibida.html',
            mensaje="Ya tiene una solicitud pendiente. Un operador le atenderá pronto.",
            exito=True
        )
    
    # 🚀 LLENAR LA COLA
        # 🚀 LLENAR LA COLA (Soporta múltiples autos)
    for i, dest in enumerate(destinos):
        tag_auto = f" [Auto {i+1}/{cantidad}]" if cantidad > 1 else ""
        nombre_final = f"{cliente.nombre}{tag_auto}"

        entrada = ColaDespacho(
            id_cliente=cliente.id_cliente,
            origen=origen,
            destino=dest,
            tarifa=0,
            estado="En espera",
            fecha_creacion=datetime.utcnow(),
            origen_solicitud="cliente_web",
            requiere_revision=requiere_revision
        )
        db.session.add(entrada)
    
    db.session.commit()

    # 🚀 AVISO EN TIEMPO REAL AL DASHBOARD
    try:
        socketio.emit('nueva_solicitud_cliente', {'msj': 'Nuevo cliente desde link web'})
        print("🔔 Evento Socket.IO 'nueva_solicitud_cliente' emitido")
    except Exception as e:
        print(f"⚠️ Error al emitir socket: {e}")

    return render_template(
        'solicitud_recibida.html',
        mensaje="¡Su solicitud fue recibida! Un operador le asignará una unidad en cuanto esté disponible.",
        exito=True
    )