from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from app import MONTO_CUOTA_SEMANAL
from extensions import db
from models.conductores import Conductor
from models.despachos import Despacho
from models.pago_cuotas import PagoCuota
from models.turnos import Turno
from models.autos import Auto
from models.puntos_espera import PuntoEspera
from sqlalchemy import func
from models.cuota_semanal import CuotaSemanal
from utils.time import hora_local
# routes/conductores.py
conductores_bp = Blueprint("conductores", __name__)  # sin url_prefix

@conductores_bp.route("/", methods=["GET"])
def listar_conductores():
    conductores = Conductor.query.all()
    resultado = [c.to_dict() for c in conductores]
    return jsonify(resultado), 200

@conductores_bp.route("/<int:id>", methods=["GET"])
def obtener_conductor(id):
    conductor = Conductor.query.get_or_404(id)
    return jsonify({
        "id_conductor": conductor.id_conductor,
        "nro_cedula": conductor.nro_cedula,
        "nombre": conductor.nombre,
        "nro_telefono": conductor.nro_telefono
    })

@conductores_bp.route('/activos', methods=['GET'])
def listar_conductores_activos():
    # Buscar turnos con estado ACTIVO
    turnos_activos = Turno.query.filter_by(estado='activo').all()
    
    # Extraer los IDs de conductores con turno activo
    ids = {t.conductor_id for t in turnos_activos}
    
    # Consultar los conductores correspondientes
    conductores = Conductor.query.filter(Conductor.id_conductor.in_(ids)).all()
    
    return jsonify([c.to_dict() for c in conductores])

@conductores_bp.route("/buscar", methods=["GET"])
def buscar_conductor():
    cedula = request.args.get("nro_cedula")
    codigo = request.args.get("codigo") # <-- Capturamos el nuevo parámetro

    query = Conductor.query

    if cedula:
        # Si llega cédula, filtramos por ella
        query = query.filter(Conductor.nro_cedula == cedula)
    elif codigo:
        # Si no hay cédula pero hay código, filtramos por código
        query = query.filter(Conductor.codigo == codigo)
    else:
        # Si no llega nada, lista vacía
        return jsonify([]), 200

    conductor = query.first()

    if conductor:
        # Usamos to_dict() que ya tienes implementado
        return jsonify([conductor.to_dict()]), 200
    
    return jsonify([]), 200

@conductores_bp.route("/", methods=["POST"])
def crear_conductor():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    # --- BLOQUE DE SEGURIDAD TOTAL (Mejorado) ---
    cedula = data.get("nro_cedula")
    codigo = data.get("codigo")
    telefono = data.get("nro_telefono")

    if cedula and Conductor.query.filter_by(nro_cedula=cedula).first():
        return jsonify({"error": f"La cédula {cedula} ya está registrada"}), 400
        
    if codigo and Conductor.query.filter_by(codigo=codigo).first():
        return jsonify({"error": f"El código {codigo} ya está asignado a otro conductor"}), 400
        
    if telefono and Conductor.query.filter_by(nro_telefono=telefono).first():
        return jsonify({"error": "El teléfono ya está registrado"}), 400
    # ---------------------------------

    try:
        nuevo = Conductor(
            codigo=codigo,
            nro_cedula=cedula,
            nombre=data.get("nombre"),
            nro_telefono=telefono,
            estado="disponible" # Valor por defecto inicial
        )
        db.session.add(nuevo)
        db.session.commit()
        
        return jsonify({
            "msg": "Conductor creado con éxito", 
            "id": nuevo.id_conductor
        }), 201

    except Exception as e:
        db.session.rollback() # Limpia la sesión si algo falla
        return jsonify({"error": "Error interno al guardar: " + str(e)}), 500

@conductores_bp.route("/<int:id>", methods=["PUT"])
def modificar_conductor(id):
    data = request.get_json()
    conductor = Conductor.query.get_or_404(id)
    if "estado" in data:
        conductor.estado = data["estado"]
    # Robustez en Cédula
    if "nro_cedula" in data and data["nro_cedula"] != conductor.nro_cedula:
        if Conductor.query.filter(Conductor.nro_cedula == data["nro_cedula"], Conductor.id_conductor != id).first():
            return jsonify({"error": "Esta cédula ya existe en otra unidad"}), 400
        conductor.nro_cedula = data["nro_cedula"]

    # Robustez en Código
    if "codigo" in data and data["codigo"] != conductor.codigo:
        if Conductor.query.filter(Conductor.codigo == data["codigo"], Conductor.id_conductor != id).first():
            return jsonify({"error": "Este código ya está asignado"}), 400
        conductor.codigo = data["codigo"]

    # Robustez en Nombre y Teléfono (Asignación directa)
    if "nombre" in data:
        conductor.nombre = data["nombre"].strip().upper()
    
    if "nro_telefono" in data:
        conductor.telefono = data["nro_telefono"]

    try:
        db.session.commit()
        return jsonify({"msg": "Datos actualizados correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@conductores_bp.route("/en_turno_disponibles", methods=["GET"])
def listar_conductores_en_turno_disponibles():
    # Buscar turnos activos
    turnos_activos = Turno.query.filter_by(estado="activo").all()
    resultado_unicos = {}

    for t in turnos_activos:
        if not t.conductor or not t.auto:
            continue

        # 🚦 Verificar si el conductor NO tiene un despacho en curso
        despacho_en_curso = (
            db.session.query(Despacho)
            .filter(
                Despacho.conductor_id == t.conductor.id_conductor,
                Despacho.estado_despacho == "en curso"
            )
            .first()
        )

        # 👉 Solo incluir si el conductor está activo y NO tiene despacho en curso
        if despacho_en_curso is None and t.conductor.estado == "activo":
            # DEBUG para confirmar que llega el código
            print("DEBUG conductor:", t.conductor.id_conductor, t.conductor.codigo, t.conductor.nombre)

            # Usamos el id_conductor como clave para evitar duplicados
            if t.conductor.id_conductor not in resultado_unicos:
                resultado_unicos[t.conductor.id_conductor] = {
                    "id_turno": t.id_turno,
                    "inicio": t.inicio.isoformat() if t.inicio else None,
                    "estado_turno": t.estado,
                    "conductor": {
                        "id_conductor": t.conductor.id_conductor,
                        "codigo": t.conductor.codigo,
                        "nombre": t.conductor.nombre,
                        "estado": t.conductor.estado
                    },
                    "auto": {
                        "id_auto": t.auto.id_auto,
                        "nro_placa": t.auto.nro_placa
                    }
                }

    # Convertimos el diccionario en lista
    return jsonify(list(resultado_unicos.values())), 200


@conductores_bp.route("/disponibles_conductores", methods=["GET"])
def listar_conductores_disponibles():
    conductores = Conductor.query.filter_by(estado="disponible").all()
    resultado = []
    
    hoy = hora_local()
    semana_actual_num = int(hoy.strftime('%U')) 
    
    for c in conductores:
        deuda_total_acumulada = semana_actual_num * MONTO_CUOTA_SEMANAL
        
        total_pagado_historico = db.session.query(db.func.sum(PagoCuota.monto_pagado))\
            .filter(PagoCuota.conductor_id == c.id_conductor).scalar() or 0.0
        
        total_historico_cuotas = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
            .filter(CuotaSemanal.conductor_id == c.id_conductor, 
                    CuotaSemanal.semana_anio == "HISTORICO-2026").scalar() or 0.0

        saldo_real = deuda_total_acumulada - (total_pagado_historico + total_historico_cuotas)
        
        if saldo_real < 0:
            saldo_real = 0.0

        permitir = getattr(c, 'permitir_deudor', 0)

        resultado.append({
            "id_conductor": c.id_conductor,
            "codigo": c.codigo,
            "nombre": c.nombre,
            "estado": c.estado,
            "saldo": float(saldo_real),
            "permitir_deudor": permitir
        })
        
    return jsonify(resultado), 200


# --- ÚNICA FUNCIÓN DE VALIDACIÓN DE SOLVENCIA ---
def es_solvente(conductor_id):
    from app import MONTO_CUOTA_SEMANAL # Importamos la tarifa global
    
    conductor = Conductor.query.get(conductor_id)
    if not conductor:
        return True, 0

    # 1. Excepción manual activa en BD
    if getattr(conductor, 'permitir_deudor', 0) == 1:
        return True, 0

    # 📊 2. AUDITORÍA CRONOLÓGICA IDENTICA A LA GRILLA
    ahora = hora_local()
    anio_actual = ahora.strftime('%Y')
    semana_actual_calendario = int(ahora.strftime('%V'))
    if semana_actual_calendario == 0:
        semana_actual_calendario = 1

    # 3. Contamos estrictamente cuántas semanas tiene saldadas (Igual que su bucle)
    semanas_saldadas = CuotaSemanal.query.filter(
        CuotaSemanal.conductor_id == conductor_id, 
        CuotaSemanal.pagado == True,
        CuotaSemanal.semana_anio.like(f"{anio_actual}-%")
    ).count()

    semanas_totales = semana_actual_calendario

    # 4. Aplicamos la misma regla de tres del Caso: DEUDOR
    if semanas_saldadas >= semanas_totales:
        # Está solvente exacto o adelantado
        return True, 0.0
    else:
        # Tiene semanas rezagadas
        semanas_debe = semanas_totales - semanas_saldadas
        saldo_calculado = float(semanas_debe * MONTO_CUOTA_SEMANAL)
        
        # Retorna False (Bloqueado) y el saldo exacto que le falta para empatar la meta
        return False, saldo_calculado

@conductores_bp.route("/en_turno", methods=["GET"])
def listar_conductores_en_turno():
    turnos = Turno.query.filter_by(estado="activo").all()
    resultado = []
    for t in turnos:
        if t.conductor and t.auto:
            resultado.append({
                "id_turno": t.id_turno,
                "inicio": t.inicio.isoformat() if t.inicio else None,
                "estado_turno": t.estado,
                "conductor": {
                    "id_conductor": t.conductor.id_conductor,
                    "nombre": t.conductor.nombre,
                    "estado": t.conductor.estado
                },
                "auto": {
                    "id_auto": t.auto.id_auto,
                    "nro_placa": t.auto.nro_placa
                }
            })
    return jsonify(resultado), 200

@conductores_bp.route("/activos_con_autos", methods=["GET"])
def listar_conductores_activos_con_autos():
    conductores = Conductor.query.filter(Conductor.estado.in_(["activo", "disponible"])).all()
    resultado = []

    for c in conductores:
        # Verificar si el conductor tiene un despacho en curso
        despacho_en_curso = Despacho.query.filter_by(conductor_id=c.id_conductor, estado_despacho="en curso").first()
        if despacho_en_curso:
            continue  # ❌ saltar este conductor porque ya está ocupado

        turno = Turno.query.filter_by(conductor_id=c.id_conductor, estado="activo").first()
        auto = turno.auto if turno else None

        # Verificar también si el auto está ocupado en un despacho en curso
        if auto:
            auto_en_curso = Despacho.query.filter_by(auto_id=auto.id_auto, estado_despacho="en curso").first()
            if auto_en_curso:
                continue  # ❌ saltar este auto porque ya está ocupado

        resultado.append({
            "conductor": {
                "id_conductor": c.id_conductor,
                "codigo": c.codigo,
                "nombre": c.nombre,
                "estado": c.estado
            },
            "auto": {
                "id_auto": auto.id_auto,
                "nro_placa": auto.nro_placa,
                "marca": auto.marca,
                "modelo": auto.modelo
            } if auto else None
        })

    return jsonify(resultado), 200

@conductores_bp.route("/actualizar_ubicacion", methods=["POST"])
def actualizar_ubicacion():
    data = request.get_json()
    if not data or 'codigo' not in data or 'latitud' not in data or 'longitud' not in data:
        return jsonify({"error": "Datos incompletos. Se requiere: codigo, latitud, longitud"}), 400

    codigo = data.get('codigo')
    lat = data.get('latitud')
    lon = data.get('longitud')

    conductor = Conductor.query.filter(
        (Conductor.codigo == codigo) | (Conductor.id_conductor == codigo)
    ).first()

    if not conductor:
        return jsonify({"error": f"Conductor con código {codigo} no encontrado"}), 404

    turno_activo = Turno.query.filter_by(
        conductor_id=conductor.id_conductor, 
        estado='activo'
    ).first()

    esta_activo = turno_activo or conductor.estado in ['activo', 'disponible', 'esperando', 'solicitando_cierre']

    if not esta_activo:
        return jsonify({
            "status": "ignorado", 
            "mensaje": "Ubicación rechazada: El conductor no tiene un turno activo"
        }), 400

    try:
        lat = float(lat)
        lon = float(lon)
        
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
             return jsonify({"error": "Coordenadas fuera de rango"}), 400
             
        conductor.latitud = lat
        conductor.longitud = lon
        conductor.ultima_actualizacion = hora_local()

        # 🔹 PERMITE RECIBIR TIEMPOS EN SIMULACIÓN
        #if 'opcion_gps' in data:
        #    conductor.opcion_gps = data['opcion_gps']

        #if data.get('expiracion_gps'):
        #    try:
        #        if isinstance(data['expiracion_gps'], str):
        #            fecha_limpia = (
        #                data['expiracion_gps'].replace('T', ' ').split('.')[0]
        #            )
        #            conductor.expiracion_gps = datetime.strptime(
        #                fecha_limpia, "%Y-%m-%d %H:%M:%S"
        #            )
        #        else:
        #            conductor.expiracion_gps = data['expiracion_gps']
        #    except Exception as e:
        #        print(f"⚠️ Error parseando expiracion_gps: {e}")
        # 👈 NOTA: Si no viene expiracion_gps en 'data', NO HACEMOS NADA y conservamos la que ya tenía guardada la base de datos.

        db.session.commit()
        return (
            jsonify(
                {"status": "éxito", "mensaje": "Ubicación actualizada correctamente"}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al guardar ubicación: " + str(e)}), 500
        
@conductores_bp.route('/conductores/en_espera', methods=['GET'])
def listar_conductores_espera():
    try:
        # Filtramos por el estado 'esperando'
        conductores = Conductor.query.filter_by(estado="esperando").all()
        # Convertimos la lista de objetos a una lista de diccionarios
        return jsonify([c.to_dict() for c in conductores]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@conductores_bp.route('/conductores/confirmar_turno/<int:id_conductor>', methods=['POST'])
def confirmar_turno(id_conductor):
    from models.conductores import Conductor
    from extensions import db
    
    conductor = Conductor.query.get_or_404(id_conductor)
    
    # Simplemente lo ponemos en disponible para que el API principal lo acepte
    conductor.estado = "disponible"
    db.session.commit()
    
    return jsonify({"status": "éxito", "mensaje": "Conductor habilitado para turno"})


@conductores_bp.route("/ubicaciones_activas", methods=["GET"])  
def obtener_ubicaciones():  
    conductores = Conductor.query.filter(  
        Conductor.estado.in_(['esperando', 'disponible', 'activo', 'solicitando_cierre'])  
    ).all()  
      
    resultado = []  
      
    for c in conductores:  
        turno_activo = Turno.query.filter_by(
            conductor_id=c.id_conductor, 
            estado='activo'
        ).first()

        id_despacho_actual = None
        try:
            despacho_activo = Despacho.query.filter_by(
                conductor_id=c.id_conductor, 
                estado_despacho='en curso'
            ).first()
            
            if despacho_activo:
                # Intentamos obtener el ID usando getattr para evitar errores si se llama 'id' o 'id_despacho'
                id_despacho_actual = getattr(despacho_activo, 'id_despacho', None) or getattr(despacho_activo, 'id', None)
        except Exception as e:
            print(f"⚠️ Error consultando despacho para conductor {c.codigo}: {e}")
            id_despacho_actual = None
        # 🟢 Extracción unificada y segura
        opcion_val = getattr(c, 'opcion_gps', None) or (getattr(turno_activo, 'opcion_gps', None) if turno_activo else None)
        exp_gps = getattr(c, 'expiracion_gps', None) or (getattr(turno_activo, 'expiracion_gps', None) if turno_activo else None)

        # Limpieza y conversión de fecha si viene como texto
        if isinstance(exp_gps, str):
            try:
                exp_gps = datetime.strptime(exp_gps.split('.')[0], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                exp_gps = None

        opcion_str = str(opcion_val or '').strip().lower()

        # 🎯 DETECCIÓN DE MODO INDEFINIDO
        es_indefinido = not opcion_str or "desactive" in opcion_str or opcion_str == "en vivo" or "hasta" in opcion_str

        if es_indefinido:
            opcion_gps_label = "Hasta que se desactive"
            exp_gps = None        
            exp_timestamp = 0     
        else:
            opcion_gps_label = str(opcion_val)
            exp_timestamp = int(exp_gps.timestamp() * 1000) if isinstance(exp_gps, datetime) else 0
        
        resultado.append({  
            "id_conductor": c.id_conductor,  
            "codigo": c.codigo,  
            "nombre": c.nombre,  
            "latitud": c.latitud,  
            "longitud": c.longitud,  
            "estado": c.estado,  
            "modo": "gps" if c.latitud is not None else "manual",  
            "expiracion_gps": exp_gps.strftime('%Y-%m-%d %H:%M:%S-04:00') if isinstance(exp_gps, datetime) else None,
            "exp_timestamp": exp_timestamp,
            "opcion_gps": opcion_gps_label,
            "ultima_actualizacion": c.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S-04:00') if isinstance(c.ultima_actualizacion, datetime) else str(c.ultima_actualizacion or ''),
            "tolerancia_dinamica_minutos": getattr(c, 'tolerancia_dinamica_minutos', 15),
            "id_despacho": id_despacho_actual # 👈 ¡ESTE ES EL CAMPO QUE FALTABA EN EL JSON!
        })  
      
    return jsonify(resultado), 200

@conductores_bp.route("/habilitar/<int:id_conductor>", methods=["POST"])
def habilitar_conductor(id_conductor):
    conductor = Conductor.query.get_or_404(id_conductor)
    # Si estaba esperando, lo pasamos a activo para que el monitoreo lo pinte de una vez
    conductor.estado = "disponible" 
    db.session.commit()
    return jsonify({"status": "éxito", "mensaje": "Conductor activado"}), 200

@conductores_bp.route("/conductor/<codigo>")
def vista_conductor(codigo):
    return render_template("conductor.html", codigo=codigo)

@conductores_bp.route('/notificar_gps/<int:id_conductor>', methods=['POST'])
def notificar_gps_manual(id_conductor):
    try:
        from models.conductores import Conductor
        from routes.telegram_bot import enviar_mensaje

        conductor = Conductor.query.get(id_conductor)
        if not conductor or not conductor.telegram_id:
            return jsonify({'status': 'error', 'mensaje': 'Conductor no encontrado o sin Telegram vinculado'}), 400

        mensaje = (
            f"🚨 <b>ALERTA DE CENTRAL - UNIDAD {conductor.codigo}</b>\n\n"
            "El operador reporta que tu ubicación en el mapa se encuentra desactualizada.\n\n"
            "📱 <b>Por favor reabre Telegram</b> para verificar que la ubicación en vivo siga activa."
        )

        enviar_mensaje(conductor.telegram_id, mensaje, parse_mode='HTML')
        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500