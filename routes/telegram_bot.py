from flask import Blueprint, request, jsonify
from datetime import datetime
import requests
import json
from flask_socketio import emit
from routes.turnos import finalizar_turno

telegram_bp = Blueprint('telegram_bp', __name__)

def emitir_al_panel(evento, datos):
    try:
        emit(evento, datos, namespace='/', broadcast=True)
        print("✅ Evento emitido con éxito usando flask_socketio.emit")
    except Exception as e:
        print(f"❌ Error al emitir evento: {e}")

def confirmar_clic(callback_id):
    TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    requests.post(url, data={'callback_query_id': callback_id})

@telegram_bp.route('/webhook', methods=['POST'])
def webhook():
    from models.conductores import Conductor
    from models.turnos import Turno
    from extensions import db
    try:
        update = request.get_json()
        print(f"DEBUG UPDATE: {update}")
        if not update:
            return jsonify({"status": "ok"}), 200

        # Identificar el mensaje de forma segura
        msg = update.get('message') or update.get('edited_message')
        if not msg:
            return jsonify({"status": "ok"}), 200
        
        chat_id = str(msg['from']['id'])
        conductor = Conductor.query.filter_by(telegram_id=chat_id).first()

       # 1. PROCESAMIENTO DE UBICACIÓN
        if 'location' in msg:
            if not conductor:
                return jsonify({"status": "ignorado_sin_conductor"}), 200
            
            # Busca directamente si la central ya le creó un turno activo
            turno_activo = Turno.query.filter_by(conductor_id=conductor.id_conductor, estado="activo").first()
            
            if turno_activo:
                conductor.latitud = msg['location']['latitude']
                conductor.longitud = msg['location']['longitude']
                conductor.ultima_actualizacion = datetime.utcnow()
                db.session.commit()
                print(f"✅ Ubicación guardada silenciosamente para {conductor.codigo}")
            else:
                print(f"⚠️ El conductor {conductor.codigo} envió ubicación pero no tiene turno activo en la web.")
            
            return jsonify({"status": "loc_actualizada"}), 200

        # 2. PROCESAMIENTO DE TEXTO
        elif 'text' in msg:
            texto = msg['text']
            
            # --- COMANDO START ---
            if texto.startswith('/start'):
                enviar_menu_botones(chat_id)
                return jsonify({"status": "menu_enviado"}), 200

            # --- BOTÓN ACTIVAR ---
            if texto == "🔗 Activar":
                if Conductor.query.filter_by(telegram_id=chat_id).first():
                    enviar_mensaje(chat_id, "✅ Ya estás vinculado al sistema.")
                    enviar_menu_botones(chat_id)
                else:
                    enviar_mensaje(chat_id, "🆔 Por favor, escribe tu código (ejemplo: B64) para activar tu cuenta.")
                return jsonify({"status": "esperando_codigo"}), 200

            # --- VALIDACIÓN DE CÓDIGO ---
            elif texto.startswith('B') and len(texto) >= 2:
                conductor_c = Conductor.query.filter_by(codigo=texto).first()
                if conductor_c:
                    if conductor_c.telegram_id and conductor_c.telegram_id != chat_id:
                        enviar_mensaje(chat_id, "⚠️ Este código ya está vinculado a otra cuenta.")
                    else:
                        conductor_c.telegram_id = chat_id
                        db.session.commit()
                        enviar_mensaje(chat_id, f"🎉 ¡Bienvenido {conductor_c.nombre}! Cuenta activada correctamente.")
                    enviar_menu_botones(chat_id)
                else:
                    enviar_mensaje(chat_id, "🚫 Código no encontrado. Contacta al operador.")
                    enviar_menu_botones(chat_id)
                return jsonify({"status": "resultado_vinculacion"}), 200

            # Si escriben cualquier otra cosa por chat
            enviar_menu_botones(chat_id)
            return jsonify({"status": "texto_procesado"}), 200

    except Exception as e:
       print(f"❌ ERROR CRÍTICO: {e}")
       return jsonify({"status": "ok"}), 200

def enviar_mensaje(chat_id, texto, parse_mode='HTML', reply_markup=None):
    TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': parse_mode
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
        
    requests.post(url, data=payload)

def enviar_menu_botones(chat_id):
    TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Menú minimalista: solo queda el botón de activación inicial
    teclado = {
        "keyboard": [
            [{"text": "🔗 Activar"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    payload = {
        'chat_id': chat_id,
        'text': "✅ Sistema de Rastreo Activo. Presiona el botón inferior si necesitas vincular tu cuenta:",
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(teclado) 
    }
    
    requests.post(url, data=payload)

def limpiar_teclado_conductor(chat_id):
    TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': "⚙️ Actualizando configuración...",
        'reply_markup': json.dumps({"remove_keyboard": True})
    }
    requests.post(url, data=payload)