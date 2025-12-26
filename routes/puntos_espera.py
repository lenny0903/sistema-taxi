from flask import Blueprint, jsonify
from models.puntos_espera import PuntoEspera

puntos_bp = Blueprint("puntos", __name__)

@puntos_bp.route("/api/puntos_espera", methods=["GET"])
def get_puntos_espera():
    puntos = PuntoEspera.query.all()
    return jsonify([p.to_dict() for p in puntos])
