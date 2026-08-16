from flask import Blueprint, request, jsonify
from models.turnos import Turno
from extensions import db
from datetime import datetime, timedelta
from models.conductores import Conductor
from models.autos import Auto
from models.despachos import Despacho
from models.puntos_espera import PuntoEspera
from routes.conductores import es_solvente
from flask_jwt_extended import get_jwt, jwt_required
from utils.time import hora_local  # Importamos la función centralizada de hora local

turnos_bp = Blueprint("turnos", __name__, url_prefix="/turnos")

# Crear turno
@turnos_bp.route('', methods=['POST']) # O simplemente @turnos_bp.route('/', methods=['POST'])
@jwt_required()
def crear_turno():
    try:
        data = request.get_json()
        conductor_id = data.get("conductor_id")
        auto_id = data.get("auto_id")
        punto_id = data.get("point_id") or data.get("punto_id")  # Soporta ambos nombres

       # --- VALIDACIÓN DE SOLVENCIA SEGÚN EL ROL ---
        claims = get_jwt()
        rol_raw = claims.get("rol_nombre") or claims.get("rol") or ""
        rol_usuario = rol_raw.lower().strip() # Forzamos a minúsculas ("administrador", "operador")
        
        # 💡 OPCIÓN B: Consultar directamente el cálculo real por semanas en mora
        solvente, saldo_pendiente = es_solvente(conductor_id)
        
        # 🎯 CONTROL ADAPTATIVO: Si sospecha que 'es_solvente' arrastra saldos fantasmas, 
        # puede sobreescribir la lógica aquí llamando a su función interna de semanas:
        # semanas = ObtenerSemanasPendientesDesdeBD(conductor_id)
        # if len(semanas) == 0:
        #     solvente = True
        #     saldo_pendiente = 0
        
        # 🚨 EL CANDADO BLINDADO: Solo bloquea si NO es solvente Y el usuario NO es admin
        if not solvente and rol_usuario not in ["administrador", "admin"]:
            # 🕵️‍♂️ Auditoría para ingeniería en la consola de la laptop:
            print(f"🚫 BLOQUEADO: Conductor {conductor_id} rechazado por saldo fantasma de ${saldo_pendiente}")
            
            return jsonify({
                "error": f"Bloqueo Administrativo: El conductor presenta un saldo deudor de ${saldo_pendiente:,.2f}."
            }), 403

        # Si el usuario es Administrador, ignorará el 'if' anterior y continuará aquí:

        # Validar que el conductor esté disponible
        conductor = Conductor.query.get(conductor_id)
        #if not conductor or conductor.estado not in ["disponible", "esperando"]:
        #    return jsonify({"error": "El conductor no ha sido habilitado por el operador"}), 400
        # Validar que el auto esté disponible
        auto = Auto.query.get(auto_id)
        # 2. Validar que ambos existan
        if not conductor or not auto:
            return jsonify({"error": "Conductor o auto no encontrado"}), 400

        # 3. Validar que el auto esté disponible
        if auto.estado != "disponible":
            return jsonify({"error": "El auto no está disponible"}), 400

        # 🛡️ 4. VALIDACIÓN BLINDADA DE COINCIDENCIA (Placa vs Código de Conductor)
        if not auto.nro_placa.lower().endswith(conductor.codigo.lower()):
            return jsonify({
                "error": f"Inconsistencia crítica: El vehículo seleccionado ({auto.nro_placa}) no corresponde a la unidad del conductor ({conductor.codigo})."
            }), 400

        # Validar que no tengan turno activo
        if Turno.query.filter_by(conductor_id=conductor_id, estado="activo").first():
            return jsonify({"error": "El conductor ya tiene un turno activo"}), 400

        if Turno.query.filter_by(auto_id=auto_id, estado="activo").first():
            return jsonify({"error": "El auto ya está en un turno activo"}), 400

        # Crear turno con punto asociado
        turno = Turno(
            conductor_id=conductor_id,
            auto_id=auto_id,
            punto_id=punto_id,
            estado="activo"
        )
        # Capturar la opción de GPS seleccionada (si no viene, usa 'hasta que desactive' por defecto)
        opcion_gps = data.get("opcion_gps", "hasta que desactive")
        ahora = hora_local()
        expiracion_gps = None

        opcion_clean = str(opcion_gps).strip().lower()

        if "15" in opcion_clean:
            expiracion_gps = ahora + timedelta(minutes=15)
        elif "1" in opcion_clean and "15" not in opcion_clean:
            expiracion_gps = ahora + timedelta(hours=1)
        elif "8" in opcion_clean:
            expiracion_gps = ahora + timedelta(hours=8)

        # Asignar al conductor
        conductor.opcion_gps = opcion_gps
        conductor.expiracion_gps = expiracion_gps
        conductor.estado = "activo"
        conductor.ultima_actualizacion = hora_local()
        conductor.alerta_enviada = False
        # Opcional: si tu modelo Turno tiene estas columnas, guardas también la copia histórica
        if hasattr(turno, 'opcion_gps'):
            turno.opcion_gps = opcion_gps
        if hasattr(turno, 'expiracion_gps'):
            turno.expiracion_gps = expiracion_gps
        # Cambiar estados
        conductor.estado = "activo"
        auto.estado = "activo"

        db.session.add(turno)
        db.session.commit()

        return jsonify({
            "msg": "Turno iniciado",
            "id_turno": turno.id_turno,
            "estado_turno": turno.estado,
            "conductor_estado": conductor.estado,
            "auto_estado": auto.estado
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al crear turno: {str(e)}")
        return jsonify({"error": str(e)}), 500



@turnos_bp.route("/<int:turno_id>/finalizar", methods=["PUT"])
def finalizar_turno(turno_id, es_bot=False):
    try:
        # 1. Búsqueda y Validación
        # Usamos db.session.get para la búsqueda por clave primaria
        turno = db.session.get(Turno, turno_id) 
        if not turno:
            return jsonify({"error": "Turno no encontrado"}), 404

        if turno.estado != "activo":
            return jsonify({"error": "El turno ya está finalizado"}), 400

        # 2. Verificación de Despachos en Curso (Lógica OK)
        despacho_activo = db.session.query(Despacho).filter(
            Despacho.conductor_id == turno.conductor_id,
            Despacho.estado_despacho == "en curso"
        ).first()

        if despacho_activo is not None:
            return jsonify({
                "error": "No se puede finalizar el turno: el conductor tiene un despacho en curso"
            }), 400

        # 3. Restaurar Auto y Conductor (Usando db.session.get para robustez)
        conductor = db.session.get(Conductor, turno.conductor_id)
        if conductor:
            conductor.estado = "disponible"
            # 💡 AQUÍ ESTÁ LA CLAVE: Limpiamos la ubicación
            conductor.latitud = None    
            conductor.longitud = None   
            # Esto hará que el filtro en 'views.py' (latitud != None) 
            # excluya a este conductor inmediatamente al recargar.
            # 💡 LIMPIEZA DE GPS: Reseteamos los campos para el próximo turno
            conductor.opcion_gps = None
            conductor.expiracion_gps = None
       # --- AQUÍ LA CORRECCIÓN ---
        # 1. Buscamos el auto relacionado (asumiendo que tu modelo Turno tiene auto_id)
        auto = db.session.get(Auto, turno.auto_id) if turno.auto_id else None
        
        # 2. Si existe, lo liberamos
        if auto:
            auto.estado = "disponible"
        # --------------------------

        turno.estado = "finalizado"
        turno.fin = hora_local()
        db.session.commit()
        # Si viene del bot, retornamos un diccionario simple, no un jsonify
        if es_bot:
            return {"success": True, "msg": "Turno finalizado"}
        
        return jsonify({"msg": "Turno finalizado"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error finalizando turno: {str(e)}"}), 500

@turnos_bp.route("/activos", methods=["GET"])
def listar_turnos_activos():
    turnos = Turno.query.filter_by(estado="activo").all()
    resultado = []
    for t in turnos:
        resultado.append({
            "id_turno": t.id_turno,
            "conductor": {
                "id_conductor": t.conductor.id_conductor,
                "codigo": t.conductor.codigo,
                "nombre": t.conductor.nombre,
                "estado": t.conductor.estado,
                # 🔹 AGREGA ESTA LÍNEA:
                "ultima_actualizacion": t.conductor.ultima_actualizacion.isoformat() if t.conductor.ultima_actualizacion else None
            } if t.conductor else None,
            "auto": {
                "id_auto": t.auto.id_auto,
                "placa": t.auto.nro_placa
            } if t.auto else None,
            "punto": {
                "id_punto": t.punto.id_punto,
                "codigo": t.punto.codigo,
                "nombre": t.punto.nombre
            } if t.punto else None,
            "inicio": t.inicio.isoformat() if t.inicio else None,
            "fin": t.fin.isoformat() if t.fin else None
        })
        
    return jsonify(resultado), 200

@turnos_bp.route("/", methods=["GET"])
def listar_turnos():
    turnos = Turno.query.all()
    return jsonify([t.to_dict() for t in turnos]), 200

@turnos_bp.route("/conductores_espera", methods=["GET"])
def conductores_en_espera():
    try:
        # Buscar turnos activos y sus relaciones
        turnos = (
            db.session.query(
                Conductor.nombre,
                Conductor.codigo,
                PuntoEspera.nombre.label("punto"),
                PuntoEspera.codigo.label("codigo_punto")
            )
            .join(Turno, Turno.conductor_id == Conductor.id_conductor)
            .join(PuntoEspera, Turno.punto_id == PuntoEspera.id_punto)
            .filter(Turno.estado == "activo")
            .all()
        )

        resultado = [
            {
                "nombre": f"{t.nombre} ({t.codigo})",
                "punto": f"{t.codigo_punto} - {t.punto}"
            }
            for t in turnos
        ]

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@turnos_bp.route("/finalizar desde mapa/<int:conductor_id>", methods=["POST"])
def finalizar_desde_mapa(conductor_id):
    # 1. Buscamos al conductor primero
    from models.conductores import Conductor
    conductor = Conductor.query.get_or_404(conductor_id)
    
    turno = Turno.query.filter_by(conductor_id=conductor_id, estado="activo").first()
    if not turno:
        return jsonify({"error": "Turno no encontrado"}), 404
    
    # 2. Ejecutamos el cierre del turno
    respuesta = finalizar_turno(turno.id_turno, es_bot=False)
    
    # 3. AQUÍ ESTÁ EL CAMBIO CLAVE:
    # Fuerza el cambio en el conductor para que salga del monitoreo
    conductor.estado = "disponible"  # O el valor que use tu lógica para "sacarlo"
    conductor.opcion_gps = None     # Limpiamos la opción para que no diga [Finalizado]
    # Si tienes estos campos, límpialos también para evitar datos residuales
    conductor.latit = None
    conductor.long = None
    
    db.session.commit() # Guardamos los cambios en el Conductor

    # 4. Emitimos al socket
    try:
        from flask import current_app
        current_app.extensions['socketio'].emit('conductor_inactivo', {'id': conductor_id})
    except Exception as e:
        print(f"⚠️ Error emitiendo socket: {e}")
        
    return respuesta