# routes/config_bot.py

from flask import Blueprint, jsonify, request

config_bp = Blueprint('config_bot', __name__)

# Esta es la variable que vive aquí y que todos consultan
MODO_AUTOMATICO = True

@config_bp.route('/api/config/estado_bot', methods=['POST'])
def configurar_bot():
    global MODO_AUTOMATICO
    data = request.get_json()
    MODO_AUTOMATICO = data.get('activo', True)
    return jsonify({"status": "éxito", "modo_automatico": MODO_AUTOMATICO})