from flask import Blueprint, request, jsonify
from extensions import db
from models.conductores import Conductor
from models.despachos import Despacho
from models.turnos import Turno
from models.autos import Auto
from models.puntos_espera import PuntoEspera
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
def buscar_conductor_por_cedula():
    cedula = request.args.get("nro_cedula")
    if not cedula:
        return jsonify([]), 200
    conductor = Conductor.query.filter_by(nro_cedula=cedula).first()
    if conductor:
        return jsonify([conductor.to_dict()]), 200
    return jsonify([]), 200

@conductores_bp.route("/", methods=["POST"])
def crear_conductor():
    data = request.get_json()

    # Validar duplicados
    if Conductor.query.filter_by(nro_cedula=data.get("nro_cedula")).first():
        return jsonify({"error": "La cédula ya está registrada"}), 400
    if Conductor.query.filter_by(nro_telefono=data.get("nro_telefono")).first():
        return jsonify({"error": "El teléfono ya está registrado"}), 400
    if Conductor.query.filter_by(codigo=data.get("codigo")).first():
        return jsonify({"error": "El código ya está registrado"}), 400

    nuevo = Conductor(
        codigo=data.get("codigo"),          # 👈 asignado por el operador
        nro_cedula=data.get("nro_cedula"),
        nombre=data.get("nombre"),
        nro_telefono=data.get("nro_telefono"),
        estado="disponible",
    )
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "msg": "Conductor creado",
        "id_conductor": nuevo.id_conductor,
        "codigo": nuevo.codigo
    }), 201


@conductores_bp.route("/<int:id>", methods=["PUT"])
def modificar_conductor(id):
    data = request.get_json()
    conductor = Conductor.query.get_or_404(id)

    # Validar duplicado de teléfono si cambia
    if "nro_telefono" in data and data["nro_telefono"] != conductor.nro_telefono:
        if Conductor.query.filter_by(nro_telefono=data["nro_telefono"]).first():
            return jsonify({"error": "El teléfono ya está registrado"}), 400
        conductor.nro_telefono = data["nro_telefono"]

    # Actualizar nombre si se envía
    if "nombre" in data:
        conductor.nombre = data["nombre"]

    db.session.commit()
    return jsonify({"msg": "Conductor actualizado", "conductor": conductor.to_dict()}), 200


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
    for c in conductores:
        resultado.append({
            "id_conductor": c.id_conductor,
            "codigo": c.codigo,
            "nombre": c.nombre,
            "estado": c.estado
        })
    return jsonify(resultado), 200



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

