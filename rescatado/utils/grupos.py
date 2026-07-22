# utils/grupos.py
from flask import Blueprint, request, jsonify
import uuid

from models.grupo import Grupo
from extensions import db   # importa la instancia correcta

grupos_bp = Blueprint("grupos", __name__)

@grupos_bp.route("/", methods=["POST"])
def crear_grupo():
    data = request.get_json()
    grupo_id = str(uuid.uuid4())[:8]
    print("DEBUG crear_grupo:", data)
    required_fields = ["cliente", "telefono", "origen", "destino", "tarifa", "num_autos"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Falta el campo requerido: {field}"}), 400

    grupo = Grupo(
        grupo_id=grupo_id,
        cliente=data["cliente"],
        telefono=data["telefono"],
        origen=data["origen"],
        destino=data["destino"],
        tarifa=data["tarifa"],
        num_autos=data["num_autos"]
    )
    
    

    db.session.add(grupo)
    db.session.commit()

    return jsonify({"grupo_id": grupo_id}), 201