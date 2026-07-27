from flask import Blueprint, request, jsonify
from datetime import datetime
import requests
import json
from flask_socketio import SocketIO
#from app import socketio # Importa la instancia desde tu app principal
from routes.turnos import finalizar_turno
telegram_bp = Blueprint('telegram_bp', __name__)

# En routes/telegram_bot.py
from flask_socketio import emit

def emitir_al_panel(evento, datos):
    try:
        # Esto emitirá el evento a todos los clientes conectados 
        # sin importar la instancia de socketio
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
        print(f"DEBUG UPDATE: {update}") # <--- Mira esto en tu consola
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
            # 1. Verificamos SIEMPRE si realmente hay un turno activo
            turno_activo = Turno.query.filter_by(conductor_id=conductor.id_conductor, estado="activo").first()
            
            # 2. Solo guardamos si el estado es 'activo' o 'en curso' Y existe un turno real
            if conductor and conductor.estado in ("activo", "en curso") and turno_activo:
                conductor.latitud = msg['location']['latitude']
                conductor.longitud = msg['location']['longitude']
                conductor.ultima_actualizacion = datetime.utcnow()
                db.session.commit()
                print(f"✅ Ubicación guardada para {conductor.codigo}")
                return jsonify({"status": "loc_actualizada"}), 200
            
            # 3. Si no cumple, se ignora silenciosamente (sin spamear al conductor)
            else:
                return jsonify({"status": "ignorado_sin_turno"}), 200
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
                    enviar_mensaje(chat_id, "✅ Ya estás activo en el sistema.")
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
                        enviar_mensaje(chat_id, f"🎉 ¡Bienvenido {conductor_c.nombre}! Cuenta activada.")
                    enviar_menu_botones(chat_id)
                else:
                    enviar_mensaje(chat_id, "🚫 Código no encontrado. Contacta al operador.")
                    enviar_menu_botones(chat_id)
                return jsonify({"status": "resultado_vinculacion"}), 200

            # --- BOTÓN INICIAR JORNADA ---
            elif texto == "📍 Iniciar Jornada":
                if not conductor:
                    enviar_mensaje(chat_id, "🚫 No estás registrado. Usa '🔗 Activar' primero.")
                else:
                    turno_activo = db.session.query(Turno).filter(
                        Turno.conductor_id == conductor.id_conductor,
                        Turno.estado == "activo"
                    ).first()

                    if turno_activo:
                        enviar_mensaje(chat_id, "⚠️ Ya tienes una jornada activa. Debes finalizarla antes de iniciar una nueva.")
                        return jsonify({"status": "error", "message": "Jornada ya activa"}), 400
                    
                    conductor.estado = "esperando"
                    db.session.commit()
                    enviar_mensaje(chat_id, "📍 Para iniciar tu jornada, por favor presiona el botón de 'Enviar Ubicación' (clip 📎).")
                
                return jsonify({"status": "esperando_ubicacion"}), 200

            # --- BOTÓN FINALIZAR JORNADA ---
            elif texto == "🛑 Finalizar Jornada":
                if not conductor:
                    enviar_mensaje(chat_id, "🚫 No estás registrado.")
                else:
                    turno_activo = Turno.query.filter_by(conductor_id=conductor.id_conductor, estado="activo").first()
                    
                    if not turno_activo:
                        enviar_mensaje(chat_id, "⚠️ No tienes ninguna jornada activa.")
                    else:
                        resultado = finalizar_turno(turno_activo.id_turno, es_bot=True)
                        
                        if resultado.get("success"):
                            msg_cierre = (
                                "🏁 *Jornada finalizada.*\n\n"
                                "Tu vehículo ha sido liberado y tu estado es 'disponible'.\n\n"
                                "⚠️ *Recuerda:* 🔗 -> Ubicación -> 'Detener ubicación'."
                            )
                            enviar_mensaje(chat_id, msg_cierre, parse_mode='Markdown')
                            print("🚀 Emitiendo evento 'turno_finalizado' al navegador...")
                            emitir_al_panel('turno_finalizado', {'conductor': conductor.nombre})
                        else:
                            enviar_mensaje(chat_id, f"❌ Error al cerrar turno: {resultado.get('error')}")
                
                enviar_menu_botones(chat_id)
                return jsonify({"status": "finalizado"}), 200

            # --- BOTÓN REINICIAR UBICACIÓN ---
            elif texto == "🛠 Reiniciar Ubicación":
                if not conductor:
                    enviar_mensaje(chat_id, "🚫 No estás registrado.")
                else:
                    instrucciones = (
                      "⚙️ *Guía de reconexión:*\n\n"
                        "1. Presiona el icono 🔗 en este chat.\n"
                        "2. Selecciona 'Ubicación' y luego pulsa 'Detener ubicación'.\n"
                        "3. Vuelve a compartir tu 'Ubicación en tiempo real' (8 horas).\n"
                        "4. Asegúrate de tener tu fecha y hora en 'Automático'."
                    )
                    enviar_mensaje(chat_id, instrucciones, parse_mode='Markdown')
                return jsonify({"status": "instrucciones_enviadas"}), 200
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
    # Si nos pasan un teclado (o el comando de quitar teclado), lo añadimos
    if reply_markup:
        payload['reply_markup'] = reply_markup
        
    requests.post(url, data=payload)


def enviar_menu_botones(chat_id):
    TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Aquí está el teclado con la nueva fila agregada:
    teclado = {
        "keyboard": [
            [{"text": "🔗 Activar"}], 
            [{"text": "📍 Iniciar Jornada"}, {"text": "🛑 Finalizar Jornada"}],
            [{"text": "🛠 Reiniciar Ubicación"}] # <--- NUEVA FILA AGREGADA
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    
    payload = {
        'chat_id': chat_id,
        'text': "✅ Bienvenido. Selecciona una acción:",
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(teclado) 
    }
    
    requests.post(url, data=payload)

def limpiar_teclado_conductor(chat_id):
    TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': "⚙️ Limpiando configuración...",
        'reply_markup': json.dumps({"remove_keyboard": True})
    }
    requests.post(url, data=payload)

def intentar_crear_turno_api(datos_turno):
    # Esta URL debe apuntar a donde vive tu función 'crear_turno' en app.py
    url_crear_turno = "http://127.0.0.1:5000/api/turnos/crear" 
    
    # --- EL ENCABEZADO QUE SALVA TU DÍA ---
    headers = {'X-Origen-Bot': 'true', 'Content-Type': 'application/json'}
    
    try:
        # Llamamos a tu API interna
        respuesta = requests.post(url_crear_turno, json=datos_turno, headers=headers)
        return respuesta
    except Exception as e:
        print(f"❌ Error al contactar la API de turnos: {e}")
        return None    