import os
import json
import requests
from datetime import datetime, timedelta
import telebot
from dotenv import load_dotenv
from flask import Flask, jsonify

# Importamos directamente la extensión de la BD y los modelos
from extensions import db
from models.conductores import Conductor
from utils.time import hora_local, TZ_CARACAS

load_dotenv()

# Creamos una mini app de Flask aislada solo para el contexto de la base de datos
test_app = Flask(__name__)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'taxis.db')
test_app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(test_app)

# Token de tu bot de pruebas
TOKEN = "8873007653:AAEFierZTs6bnTvpMBbsVuIE6Af2ZZvkZWo"
bot = telebot.TeleBot(TOKEN)

def enviar_mensaje(chat_id, texto, parse_mode='HTML', reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': texto,
            'parse_mode': parse_mode
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"❌ Error al enviar mensaje a Telegram: {e}")

def enviar_menu_botones(chat_id):
    try:
        teclado = {
            "keyboard": [
                [{"text": "🔗 Activar"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': "✅ Sistema de Rastreo Activo. Presiona el botón inferior si necesitas vincular tu cuenta:",
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(teclado) 
        }
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"❌ Error al enviar menú de botones: {e}")

@bot.message_handler(content_types=['text', 'location'])
def procesar_actualizacion_telegram(message):
    chat_id = str(message.chat.id)
    msg = message.json
    if not msg:
        return

    if msg.get('from', {}).get('is_bot', False):
        return

    with test_app.app_context():
        try: 
            print(f"DEBUG UPDATE: {msg}") 

            # 1. Identificar el mensaje de forma segura (ya lo tenemos en msg)
            chat_id = str(msg['from']['id']) 

            # 2. PROCESAMIENTO DE TEXTO PRIMERO
            if 'text' in msg: 
                texto = msg['text'] 
                
                if texto.startswith('/start'): 
                    enviar_menu_botones(chat_id) 
                    return

                if texto == "🔗 Activar": 
                    conductor_temp = Conductor.query.filter_by(telegram_id=chat_id).first() 
                    if conductor_temp: 
                        enviar_mensaje(chat_id, "✅ Ya estás vinculado al sistema.") 
                    else: 
                        enviar_mensaje(chat_id, "🆔 Por favor, escribe tu código (ejemplo: B64) para activar tu cuenta.") 
                    enviar_menu_botones(chat_id) 
                    return

                elif texto.upper().startswith('B') and len(texto) > 1 and texto.upper()[1:].isdigit(): 
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
                    return

                enviar_menu_botones(chat_id) 
                return

            # 3. BUSCAR AL CONDUCTOR
            conductor = Conductor.query.filter_by(telegram_id=chat_id).first() 

            if not conductor: 
                print(f"⚠️ Telegram ID {chat_id} no encontrado en la BD") 
                enviar_mensaje(chat_id, "🆔 Bienvenido. Por favor, presiona el botón de abajo o escribe tu código de control:") 
                enviar_menu_botones(chat_id) 
                return

            # 4. PROCESAMIENTO DE UBICACIÓN
            if "location" in msg: 
                ahora = hora_local()  

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
                print(f"📍 Ubicación actualizada para {conductor.nombre}")
                return

            enviar_menu_botones(chat_id) 

        except Exception as e: 
            print(f"❌ ERROR CRÍTICO: {e}")
if __name__ == "__main__":
    print("🚀 Bot de pruebas conectado directo a taxis.db corriendo en modo Polling...")
    bot.infinity_polling()