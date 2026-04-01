from flask import Blueprint, request, jsonify
from extensions import db
from models.autos import Auto
from models.turnos import Turno

autos_bp = Blueprint("autos", __name__, url_prefix="/autos")

@autos_bp.route("/", methods=["POST"])
def crear_auto():
    try:
        data = request.get_json()
        # Normalizamos la placa a mayúsculas para comparar
        placa = data.get("nro_placa", "").strip().upper()

        # VALIDACIÓN MANUAL ANTES DE INSERTAR
        existente = Auto.query.filter_by(nro_placa=placa).first()
        if existente:
            # Aquí devolvemos 400, que es un error "esperado" y no un colapso del servidor
            return jsonify({"error": f"La placa {placa} ya existe en el sistema"}), 400

        nuevo = Auto(
            nro_placa=placa,
            tipo_auto=data.get("tipo_auto"),
            marca=data.get("marca"),
            modelo=data.get("modelo"),
            estado="disponible"
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify(nuevo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error inesperado: " + str(e)}), 500

@autos_bp.route("/", methods=["GET"])
def listar_autos():
    autos = Auto.query.all()
    return jsonify([a.to_dict() for a in autos])

@autos_bp.route("/<int:id>", methods=["GET"])
def obtener_auto(id):
    auto = Auto.query.get_or_404(id)
    return jsonify({
        "id_auto": auto.id_auto,
        "placa": auto.nro_placa,
        "tipo_auto": auto.tipo_auto,
        "marca": auto.marca,
        "modelo": auto.modelo
    })

@autos_bp.route('/activos', methods=['GET'])
def listar_autos_activos():
    turnos_activos = Turno.query.filter_by(estado='activo').all()
    ids = {t.auto_id for t in turnos_activos}
    print("Turnos activos:", turnos_activos)
    print("IDs de autos activos:", ids)
    autos = Auto.query.filter(Auto.id_auto.in_(ids)).all()
    print("Autos encontrados:", autos)
    return jsonify([a.to_dict() for a in autos])

@autos_bp.route("/buscar", methods=["GET"])
def buscar_auto_por_placa():
    placa = request.args.get("placa", "").strip() # Limpiamos espacios
    if not placa:
        return jsonify([]), 200

    auto = Auto.query.filter_by(nro_placa=placa).first()
    if auto:
        # IMPORTANTE: Usamos los nombres que el JS buscará
        return jsonify([{
            "id_auto": auto.id_auto,
            "nro_placa": auto.nro_placa, # Cambiado de "placa" a "nro_placa"
            "tipo_auto": auto.tipo_auto,
            "marca": auto.marca,
            "modelo": auto.modelo
        }]), 200

    return jsonify([]), 200

@autos_bp.route("/<int:id>", methods=["PUT"])
def modificar_auto(id):
    try:
        data = request.get_json()
        auto = Auto.query.get_or_404(id)

        # 1. Validación de Placa (Si se envía una nueva placa)
        if "nro_placa" in data:
            nueva_placa = data["nro_placa"].strip().upper()
            
            # Verificar que la placa no la tenga OTRO auto
            existente = Auto.query.filter(Auto.nro_placa == nueva_placa, Auto.id_auto != id).first()
            if existente:
                return jsonify({"error": f"La placa {nueva_placa} ya está registrada en otro vehículo"}), 400
            
            auto.nro_placa = nueva_placa

        # 2. Actualización de los demás campos
        if "tipo_auto" in data: auto.tipo_auto = data["tipo_auto"]
        if "marca" in data: auto.marca = data["marca"]
        if "modelo" in data: auto.modelo = data["modelo"]

        db.session.commit()
        return jsonify(auto.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error al modificar: {e}")
        return jsonify({"error": "No se pudo actualizar el vehículo"}), 500

@autos_bp.route("/disponibles", methods=["GET"])
def listar_autos_disponibles():
     try:
        # Autos que están en estado Disponible y no tienen turno activo
        autos_ocupados = db.session.query(Turno.auto_id).filter(Turno.estado == "activo")
        autos = Auto.query.filter(~Auto.id_auto.in_(autos_ocupados)).filter_by(estado="disponible").all()

        resultado = [
            {
                "id_auto": a.id_auto,
                "placa": a.nro_placa,
                "marca": a.marca,
                "modelo": a.modelo,
                "estado": a.estado
            }
            for a in autos
        ]
        return jsonify(resultado), 200
     except Exception as e:
         return jsonify({"error": str(e)}), 500

@autos_bp.route("/disponibles/<int:conductor_id>", methods=["GET"])
def listar_auto_por_conductor(conductor_id):
    try:
        # Buscar turno activo del conductor
        turno = Turno.query.filter_by(conductor_id=conductor_id, estado="activo").first()
        if not turno:
            return jsonify([]), 200

        auto = Auto.query.get(turno.auto_id)
        if not auto:
            return jsonify([]), 200

        return jsonify([{
            "id_auto": auto.id_auto,
            "placa": auto.nro_placa,
            "marca": auto.marca,
            "modelo": auto.modelo,
            "estado": auto.estado
        }]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
