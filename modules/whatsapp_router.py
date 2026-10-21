import os
from flask import Blueprint, request, jsonify
from modules.adapters.meta_adapter import parse_meta_payload, send_meta_message
from modules.adapters.green_api_adapter import parse_green_api_payload, send_green_api_message
from modules.bot_logic import procesar_logica_negocio as procesar_bot_real

# 👉 Importa aquí tu máquina de estados o lógica de negocio real:
# from modules.bot_logic import procesar_logica_negocio

whatsapp_bp = Blueprint('whatsapp', __name__)

# Lee el proveedor desde el archivo .env (meta o green_api)
PROVIDER = os.getenv("WHATSAPP_PROVIDER", "meta").lower()

def enviar_mensaje(chat_id, texto):
    if PROVIDER == "meta":
        return send_meta_message(chat_id, texto)
    else:
        return send_green_api_message(chat_id, texto)

# 🟢 Función provisional (puedes reemplazarla o importarla desde tu módulo de lógica)
def procesar_logica_negocio(evento, enviar_func):
    procesar_bot_real(evento, enviar_func)
    print("========================================", flush=True)
    print("📥 EVENTO RECIBIDO:", evento, flush=True)
    print("========================================", flush=True)
    
    chat_id = evento.get("chat_id")
    texto = evento.get("texto", "").lower()
    
    if "hola" in texto:
        enviar_func(chat_id, "¡Bienvenido a Taxis Táchira! Por favor, comparte tu ubicación GPS para pedir un servicio.")
    else:
        enviar_func(chat_id, f"Mensaje recibido correctamente: {texto}")
@whatsapp_bp.route('/api/whatsapp/webhook', methods=['POST'])
def webhook_universal():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "ignored"}), 200

    # Normalizar datos según el proveedor activo
    if PROVIDER == "meta":
        evento = parse_meta_payload(data)
    else:
        evento = parse_green_api_payload(data)

    if evento:
        # evento trae: chat_id, telefono, nombre, tipo_msg, contenido/lat/lng
        procesar_logica_negocio(evento, enviar_mensaje)

    return jsonify({"status": "received"}), 200