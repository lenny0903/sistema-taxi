from flask import Blueprint, request, jsonify
from models.turnos import Turno
from extensions import db
from datetime import datetime
from models.conductores import Conductor
from models.autos import Auto
from models.despachos import Despacho
from models.puntos_espera import PuntoEspera
from routes.conductores import es_solvente
from flask_jwt_extended import get_jwt, jwt_required


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
        rol_usuario = claims.get("rol_nombre") or claims.get("rol")  # Captura "Administrador" u "Operador"
        
        solvente, saldo_pendiente = es_solvente(conductor_id)
        
        # 🚨 EL CAMBIO CLAVE: Solo bloqueamos si NO es solvente Y el usuario NO es Administrador.
        if not solvente and rol_usuario != "Administrador":
            return jsonify({
                "error": f"Bloqueo Administrativo: El conductor presenta un saldo deudor de ${saldo_pendiente:,.2f}."
            }), 403

        # Si el usuario es Administrador, ignorará el 'if' anterior y continuará aquí:

        # Validar que el conductor esté disponible
        conductor = Conductor.query.get(conductor_id)
        if not conductor or conductor.estado != "disponible":
            return jsonify({"error": "El conductor no está disponible"}), 400

        # Validar que el auto esté disponible
        auto = Auto.query.get(auto_id)
        if not auto or auto.estado != "disponible":
            return jsonify({"error": "El auto no está disponible"}), 400

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
def finalizar_turno(turno_id):
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
            # 💡 No es necesario db.session.add aquí, commit lo hará si es persistente

        auto = db.session.get(Auto, turno.auto_id)
        if auto:
            auto.estado = "disponible"
            # 💡 No es necesario db.session.add aquí

        # 4. Finalizar Turno y Persistencia
        turno.estado = "finalizado"
        turno.fin = datetime.utcnow()
        # db.session.add(turno) # El objeto 'turno' ya está en la sesión, no es necesario re-añadir

        # 5. Commit y Liberación de Recursos
        db.session.commit() # 💥 El fallo ocurre aquí si hay un problema de mapeo

        # Respuesta
        return jsonify({
            "msg": "Turno finalizado",
            "id_turno": turno.id_turno,
            "estado_turno": turno.estado,
            "conductor_estado": conductor.estado if conductor else None,
            "auto_estado": auto.estado if auto else None
        }), 200

    except Exception as e:
        # 6. Rollback y Manejo de Error (IMPORTANTE: Verifique si hay triggers)
        db.session.rollback()
        
        # 💡 Este error indica que el objeto (Turno, Conductor o Auto) 
        # está intentando actualizarse de una manera que la BD no permite.
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
                "estado": t.conductor.estado
            } if t.conductor else None,
            "auto": {
                "id_auto": t.auto.id_auto,
                "placa": t.auto.nro_placa
            } if t.auto else None,
            "punto": {
                "id_punto": t.punto.id_punto,
                "codigo": t.punto.codigo,
                "nombre": t.punto.nombre
            } if t.punto else None,   # 🔹 nuevo bloque
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