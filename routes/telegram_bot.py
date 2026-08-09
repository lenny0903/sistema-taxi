from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import requests
import json
import os
import pytz
from flask_socketio import emit
from routes.turnos import finalizar_turno
from utils.time import hora_local
from dotenv import load_dotenv

load_dotenv()
telegram_bp = Blueprint('telegram_bp', __name__)


def emitir_al_panel(evento, datos):
    try:
        emit(evento, datos, namespace='/', broadcast=True)
        print("✅ Evento emitido con éxito usando flask_socketio.emit")
    except Exception as e:
        print(f"❌ Error al emitir evento: {e}")

def confirmar_clic(callback_id):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    requests.post(url, data={'callback_query_id': callback_id})


@telegram_bp.route('/webhook', methods=['POST'])
def webhook():
    from models.conductores import Conductor
    from models.turnos import Turno
    from extensions import db
    print("--- LLEGÓ PETICIÓN DE TELEGRAM ---")
    print("RAW DATA:", request.data)
    try:
        update = request.get_json()
        print(f"DEBUG UPDATE: {update}")
        if not update:
            return jsonify({"status": "ok"}), 200

        # 1. Identificar el mensaje de forma segura
        msg = update.get('message') or update.get('edited_message')
        if not msg:
            return jsonify({"status": "sin_mensaje"}), 200

        chat_id = str(msg['from']['id'])

        # 2. PROCESAMIENTO DE TEXTO (Lo subimos para que los no registrados puedan enviar su código Bxx o /start)
        if 'text' in msg:
            texto = msg['text']
            
            # --- COMANDO START ---
            if texto.startswith('/start'):
                enviar_menu_botones(chat_id)
                return jsonify({"status": "menu_enviado"}), 200

            # --- BOTÓN ACTIVAR ---
            if texto == "🔗 Activar":
                conductor_temp = Conductor.query.filter_by(telegram_id=chat_id).first()
                if conductor_temp:
                    enviar_mensaje(chat_id, "✅ Ya estás vinculado al sistema.")
                    enviar_menu_botones(chat_id)
                else:
                    enviar_mensaje(chat_id, "🆔 Por favor, escribe tu código (ejemplo: B64) para activar tu cuenta.")
                    enviar_menu_botones(chat_id)
                return jsonify({"status": "esperando_codigo"}), 200

            # --- VALIDACIÓN DE CÓDIGO ---
            elif texto.upper().startswith('B') and len(texto) >= 2:
                codigo_buscado = texto.upper()
                conductor_c = Conductor.query.filter_by(codigo=codigo_buscado).first()
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

            enviar_menu_botones(chat_id)
            return jsonify({"status": "texto_procesado"}), 200

        # 3. BUSCAR AL CONDUCTOR PRIMERO (Para funciones como ubicación que exigen estar registrado)
        conductor = Conductor.query.filter_by(telegram_id=chat_id).first()

        if not conductor:
            print(f"⚠️ Telegram ID {chat_id} no encontrado en la BD")
            
            # 🛡️ BLINDAJE ANTISPAM: Si un usuario no registrado manda ubicación, 
            # la ignoramos silenciosamente para evitar que el bucle de Live Location sature el chat.
            if "location" in msg:
                return jsonify({"status": "ubicacion_ignorada_sin_registro"}), 200

            enviar_mensaje(chat_id, "🆔 Bienvenido. Por favor, presiona el botón de abajo o escribe tu código de control:")
            enviar_menu_botones(chat_id)
            return jsonify({"status": "conductor_no_encontrado"}), 200

        # 4. PROCESAMIENTO DE UBICACIÓN (Normal, Live Location o Cierre Manual)
        
        # 🛑 DETECCIÓN DE CIERRE MANUAL: 
        # Si es un mensaje editado y la ubicación ya no tiene 'live_period' (o no viene la ubicación)
        es_cierre_manual = False
        if "edited_message" in update:
            if "location" not in msg:
                es_cierre_manual = True
            elif "location" in msg and "live_period" not in msg["location"]:
                es_cierre_manual = True

        if es_cierre_manual:
            ahora = hora_local()
            conductor.expiracion_gps = ahora
            conductor.opcion_gps = "Finalizado"

            if hasattr(conductor, "turno_activo") and conductor.turno_activo:
                conductor.turno_activo.expiracion_gps = ahora
                conductor.turno_activo.opcion_gps = "Finalizado"

            db.session.commit()
            
            enviar_mensaje(chat_id, "🛑 Has dejado de compartir tu ubicación. Sesión de GPS finalizada correctamente.")
            enviar_menu_botones(chat_id)
            print(f"🛑 [GPS] El conductor {conductor.codigo} finalizó su GPS manualmente.")
            return jsonify({"status": "loc_finalizada_manual"}), 200

        # --- PROCESAMIENTO DE UBICACIÓN ACTIVA (Cuando sí trae coordenadas) ---
        if "location" in msg:
            ahora = hora_local()  # Fecha con zona horaria (aware)

            conductor.latitud = msg["location"]["latitude"]
            conductor.longitud = msg["location"]["longitude"]
            conductor.ultima_actualizacion = ahora
            conductor.alerta_enviada = False
            
            segundos = msg["location"].get("live_period")

            exp_db = conductor.expiracion_gps
            if exp_db and exp_db.tzinfo is None:
                from utils.time import TZ_CARACAS
                exp_db = exp_db.replace(tzinfo=TZ_CARACAS)

            expirado = not exp_db or exp_db < ahora

            if expirado:
                duracion = segundos or 28800
                opciones = {900: "15 min", 3600: "1 hora", 28800: "8 horas"}
                
                if duracion in opciones:
                    conductor.opcion_gps = opciones[duracion]
                else:
                    duracion = 28800
                    conductor.opcion_gps = "8 horas"

                conductor.expiracion_gps = ahora + timedelta(seconds=duracion)

            if hasattr(conductor, "turno_activo") and conductor.turno_activo:
                conductor.turno_activo.expiracion_gps = conductor.expiracion_gps
                conductor.turno_activo.opcion_gps = conductor.opcion_gps

            db.session.commit()
            return jsonify({"status": "loc_actualizada"}), 200

        # 🛡️ CIERRE SEGURO Y SILENCIOSO: 
        # Si llega cualquier otra actualización que no sea texto ni ubicación activa.
        return jsonify({"status": "actualizacion_silenciada"}), 200

    except Exception as e:
       print(f"❌ ERROR CRÍTICO: {e}")
       return jsonify({"status": "error", "detalle": str(e)}), 500
    
        
def enviar_mensaje(chat_id, texto, parse_mode='HTML', reply_markup=None):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
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
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
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
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': "⚙️ Actualizando configuración...",
        'reply_markup': json.dumps({"remove_keyboard": True})
    }
    requests.post(url, data=payload)