from flask import Blueprint, request, jsonify
from services.telegram_service import procesar_update_telegram
from utils.notificaciones import enviar_mensaje_con_teclado_inline
from models.despachos import Despacho
from models.conductores import Conductor

telegram_bp = Blueprint('telegram_bp', __name__)

@telegram_bp.route('/webhook', methods=['POST'])
def webhook():
    print("--- LLEGÓ PETICIÓN DE TELEGRAM ---")
    try:
        update = request.get_json()
        if not update:
            return jsonify({"status": "ok"}), 200
        
        resultado, status_code = procesar_update_telegram(update)
        return jsonify(resultado), status_code

    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN WEBHOOK: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "detalle": str(e)}), 200


def publicar_en_canal(id_despacho):
    despacho = Despacho.query.get(id_despacho)
    if not despacho:
        print(f"⚠️ Despacho #{id_despacho} no encontrado.")
        return

    conductor = Conductor.query.get(despacho.conductor_id) if despacho.conductor_id else None
    nro_ctrl = conductor.codigo if conductor else "Unidad"
    nombre_cond = conductor.nombre if conductor else "Conductor"

    url_bot = f"https://t.me/Lospatriotas_bot?start=srv-{id_despacho}"
    teclado = {
        "inline_keyboard": [
            [{"text": "🚗 Ver mi viaje", "url": url_bot}]
        ]
    }

    mensaje = (
        f"🚖 *Nuevo servicio disponible*\n\n"
        f"📋 Despacho #{id_despacho}\n"
        f"🚗 Unidad: #{nro_ctrl}\n"
        f"👤 Conductor: {nombre_cond}\n\n"
        "🔹 Haz clic en el botón para rastrear tu viaje en tiempo real."
    )

    enviar_mensaje_con_teclado_inline("@Lospatriotasdetariba", mensaje, teclado)
    print(f"📢 Mensaje publicado en el canal para el Despacho #{id_despacho}")