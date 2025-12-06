from flask import Blueprint, request, jsonify
from extensions import db
from models.autos import Auto
from models.turnos import Turno

autos_bp = Blueprint("autos", __name__, url_prefix="/autos")

@autos_bp.route("/", methods=["POST"])
def crear_auto():
    data = request.get_json()
    nuevo = Auto(
        nro_placa=data.get("placa"),
        tipo_auto=data.get("tipo_auto"),
        marca=data.get("marca"),
        modelo=data.get("modelo")
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"msg": "Auto creado", "id_auto": nuevo.id_auto}), 201

@autos_bp.route("/", methods=["GET"])
def listar_autos():
    autos = Auto.query.all()
    resultado = [
        {"id_auto": a.id_auto, "placa": a.nro_placa, "tipo_auto": a.tipo_auto, "marca": a.marca, "modelo": a.modelo}
        for a in autos
    ]
    return jsonify(resultado), 200

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
    placa = request.args.get("placa")
    if not placa:
        return jsonify([]), 200

    auto = Auto.query.filter_by(nro_placa=placa).first()
    if auto:
        return jsonify([{
            "id_auto": auto.id_auto,
            "placa": auto.nro_placa,
            "tipo_auto": auto.tipo_auto,
            "marca": auto.marca,
            "modelo": auto.modelo
        }]), 200

    return jsonify([]), 200

@autos_bp.route("/<int:id>", methods=["PUT"])
def modificar_auto(id):
    data = request.get_json()
    auto = Auto.query.get_or_404(id)

    if "tipo_auto" in data:
        auto.tipo_auto = data["tipo_auto"]
    if "marca" in data:
        auto.marca = data["marca"]
    if "modelo" in data:
        auto.modelo = data["modelo"]

    db.session.commit()
    return jsonify(auto.to_dict()), 200
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

