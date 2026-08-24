from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import requests
import json
import os
import pytz
from flask_socketio import emit
from flask import url_for
#from rescatado.models import Despacho
from routes.turnos import finalizar_turno
from utils.time import hora_local
from utils.notificaciones import enviar_mensaje, enviar_menu_botones, enviar_mensaje_con_teclado_inline
from models.despachos import Despacho
from dotenv import load_dotenv

load_dotenv()
telegram_bp = Blueprint('telegram_bp', __name__)

usuarios_reportando = {}
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

        # 0. 🔘 PROCESAMIENTO DE CLICS EN BOTONES (ENCUESTA DEL CLIENTE)
        callback = update.get('callback_query')
        if callback:
            data = callback.get('data') # Ej: 'cal_123_5'
            chat_id = str(callback['from']['id'])
            callback_id = callback['id']
            
            if data and data.startswith('cal_'):
                try:
                    _, id_despacho_str, calificacion_str = data.split('_')
                    id_despacho = int(id_despacho_str)
                    estrellas = int(calificacion_str)

                    # 🌟 GUARDAR EN LA BASE DE DATOS
                    despacho = Despacho.query.get(id_despacho)
                    if despacho:
                        despacho.calificacion = estrellas
                        despacho.fecha_calificacion = datetime.now()
                        despacho.telegram_id_cliente = chat_id
                        db.session.commit()
                        print(f"⭐ Calificación guardada: Despacho #{id_despacho} con {estrellas} estrellas")
                    else:
                        print(f"⚠️ Despacho #{id_despacho} no encontrado para la calificación.")

                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Error al guardar calificación en DB: {e}")

                # Responder al clic para quitar el estado de carga del botón
                confirmar_clic(callback_id)
                
                # 🚨 NUEVO: Si marca 1 estrella (Inconveniente), activamos el modo reporte
                if estrellas == 1:
                    usuarios_reportando[chat_id] = id_despacho
                    enviar_mensaje(
                        chat_id, 
                        "⚠️ Lamentamos mucho el inconveniente. Por favor, **escribe en un breve mensaje qué sucedió** "
                        "para reportarlo de inmediato con la administración."
                    )
                    return jsonify({"status": "esperando_comentario_inconveniente"}), 200
                else:
                    # Para las demás calificaciones, mensaje normal de agradecimiento
                    enviar_mensaje(chat_id, "✅ ¡Muchas gracias por tu opinión! Nos ayuda a mejorar el servicio.")
                    return jsonify({"status": "encuesta_recibida"}), 200

        # 1. Identificar el mensaje de forma segura
        msg = update.get('message') or update.get('edited_message')
        if not msg:
            return jsonify({"status": "sin_mensaje"}), 200

        user_from = msg.get('from')
        if not user_from or 'id' not in user_from:
            return jsonify({"status": "sin_remitente_valido"}), 200
        chat_id = str(user_from['id'])

        # 2. PROCESAMIENTO DE TEXTO
        if 'text' in msg:
            texto = msg['text']
            
            # 📝 NUEVO: ¿El usuario está escribiendo un reporte de inconveniente pendiente?
            if chat_id in usuarios_reportando:
                id_despacho = usuarios_reportando.pop(chat_id) # Extrae y borra del diccionario para liberar el estado
                try:
                    despacho = Despacho.query.get(id_despacho)
                    if despacho:
                        despacho.comentario_calificacion = texto
                        db.session.commit()
                        print(f"📝 [REPORTE] Comentario guardado para Despacho #{id_despacho}: {texto}")
                    else:
                        print(f"⚠️ [REPORTE] Despacho #{id_despacho} no encontrado para guardar el comentario.")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Error al guardar comentario de inconveniente: {e}")

                enviar_mensaje(chat_id, "✅ Reporte recibido. Muchas gracias por ayudarnos a mejorar. ¡Feliz día!")
                return jsonify({"status": "comentario_inconveniente_guardado"}), 200

            # --- COMANDO START ---
            # --- COMANDO START ---
            if texto.startswith('/start'):
                partes = texto.split(' ')
                if len(partes) > 1:
                    servicio_id = partes[1].replace('srv-', '')
                    try:
                        id_despacho = int(servicio_id)
                        despacho = Despacho.query.get(id_despacho)
                        
                        if despacho:
                            despacho.telegram_id_cliente = chat_id
                            db.session.commit()
                            print(f"🔗 [TELEGRAM] Cliente {chat_id} vinculado al Despacho #{id_despacho}")
                            conductor_asig = db.session.get(Conductor, despacho.conductor_id) if hasattr(despacho, 'conductor_id') and despacho.conductor_id else None
                            nro_ctrl = conductor_asig.codigo if conductor_asig else "Unidad"
                            nombre_cond = conductor_asig.nombre if conductor_asig else "Conductor asignado"
                            
                            # ✅ AQUÍ USAMOS LA URL DINÁMICA DE CLOUDFLARE IGUAL QUE EN "UBI"
                            base_url = request.host_url.rstrip('/')
                            url_mapa = url_for('views_bp.pagina_mapa_despacho', id_despacho=id_despacho, _external=True)
                            
                            teclado_cliente = {
                                "inline_keyboard": [
                                    [{"text": "🗺️ Ver Mapa en Tiempo Real", "url": url_mapa}]
                                ]
                            }
                            
                            mensaje_cliente = (
                                f"📍 *¡Hola! Aquí tienes el rastreo de tu servicio #{id_despacho}*\n\n"
                                f"🚗 Unidad: #{nro_ctrl}\n"
                                f"👤 Conductor: {nombre_cond}\n\n"
                                "Haz clic en el botón de abajo para seguir el recorrido en vivo:"
                            )
                            
                            enviar_mensaje_con_teclado_inline(chat_id, mensaje_cliente, teclado_cliente)
                        else:
                            enviar_mensaje(chat_id, "⚠️ No encontramos los datos de este servicio.")
                    except Exception as e:
                        print(f"❌ Error al procesar start de cliente: {e}")
                        enviar_mensaje(chat_id, "❌ Ocurrió un error al procesar tu solicitud de rastreo.")
                    
                    return jsonify({"status": "menu_client_enviado"}), 200
                else:
                    enviar_menu_botones(chat_id)
                    return jsonify({"status": "menu_enviado"}), 200
            # 📍 Palabra clave "UBI"
            if texto.strip().upper() == "UBI":
                print("🎯 [WEBHOOK] ¡ATRAPÓ EL UBI!")
                
                despacho_reciente = Despacho.query.order_by(Despacho.id_despacho.desc()).first()
                
                if despacho_reciente:
                    despacho_reciente.telegram_id_cliente = chat_id
                    db.session.commit()
                    conductor_asig = db.session.get(Conductor, despacho_reciente.conductor_id) if hasattr(despacho_reciente, 'conductor_id') and despacho_reciente.conductor_id else None
                    nro_ctrl = conductor_asig.codigo if conductor_asig else "Unidad"
                    nombre_cond = conductor_asig.nombre if conductor_asig else "Conductor"
                    
                    # Extrae la URL base automáticamente (sea Cloudflare o local)
                    base_url = request.host_url.rstrip('/')
                    enlace_mapa = f"{base_url}/monitoreo/{despacho_reciente.id_despacho}"
                    
                    mensaje_ubi = (
                        f"📍 Rastreo activo (Despacho #{despacho_reciente.id_despacho})\n\n"
                        f"🚗 Unidad: #{nro_ctrl}\n"
                        f"👤 Conductor: {nombre_cond}\n\n"
                        f"🗺️ Ver mapa en tiempo real:\n{enlace_mapa}"
                    )
                    enviar_mensaje(chat_id, mensaje_ubi, parse_mode=None)
                else:
                    enviar_mensaje(chat_id, "⚠️ No tienes ningún servicio activo registrado en este momento.", parse_mode=None)
                return jsonify({"status": "ubi_procesado"}), 200
            # --- BOTÓN ACTIVAR (Conductores) ---
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
        if "edited_message" in update and "location" in msg:
            if "live_period" not in msg["location"]:
                es_cierre_manual = True

        if es_cierre_manual:
            ahora = hora_local()
            conductor.expiracion_gps = ahora
            conductor.opcion_gps = "Finalizado"

            if hasattr(conductor, "turno_activo") and conductor.turno_activo:
                conductor.turno_activo.expiracion_gps = ahora
                conductor.turno_activo.opcion_gps = "Finalizado"

            db.session.commit()
            
            # Emitir evento al panel en tiempo real
            emitir_al_panel('conductor_inactivo', {
                'conductor_id': conductor.id_conductor,
                'codigo': conductor.codigo
            })
            
            enviar_mensaje(chat_id, "🛑 Has dejado de compartir tu ubicación. Sesión de GPS finalizada correctamente.")
            enviar_menu_botones(chat_id)
            print(f"🛑 [GPS] El conductor {conductor.codigo} finalizó su GPS manualmente.")
            return jsonify({"status": "loc_finalizada_manual"}), 200

        # --- PROCESAMIENTO DE UBICACIÓN ACTIVA (Cuando sí trae coordenadas) ---
        if "location" in msg:
            print(">>> LLEGÓ UNA UBICACIÓN DESDE TELEGRAM <<<")
            print(">>> CONTENIDO COMPLETO DE LOCATION:", msg["location"])
            # 🚨 🛑 FILTRO: Validar que NO envíe ubicación fija (estática). 
            # Si el mensaje no viene de un mensaje editado y carece de 'live_period', es una ubicación estática compartida por error.
            if "edited_message" not in update and "live_period" not in msg["location"]:
                enviar_mensaje(
                    chat_id, 
                    "⚠️ *Error de Ubicación*\n\n"
                    "Has enviado una ubicación fija. Para estar activo en el mapa de la central debes compartir tu **'Ubicación en tiempo real'**.\n\n"
                    "Por favor vuelve a intentarlo seleccionando el tiempo deseado."
                )
                enviar_menu_botones(chat_id)
                print(f"⚠️ [GPS] El conductor {conductor.codigo} intentó enviar ubicación estática (Rechazado).")
                return jsonify({"status": "ubicacion_estatica_rechazada"}), 200

            # 🟢 SI PASA LA VALIDACIÓN: ES UBICACIÓN EN TIEMPO REAL (LIVE LOCATION)
            # 🟢 AL PROCESAR LA UBICACIÓN:
            ahora = hora_local().replace(microsecond=0)  # 🔥 TRUNCAR MICROSEGUNDOS

            conductor.latitud = msg["location"]["latitude"]
            conductor.longitud = msg["location"]["longitude"]
            conductor.ultima_actualizacion = ahora
            conductor.alerta_enviada = False

            segundos = msg["location"].get("live_period")

            # Determinar la opción elegida según los segundos
            if segundos == 900:
                nueva_opcion = "15 min"
                nueva_duracion_seg = 900
            elif segundos == 3600:
                nueva_opcion = "1 hora"
                nueva_duracion_seg = 3600
            elif segundos == 28800:
                nueva_opcion = "8 horas"
                nueva_duracion_seg = 28800
            else:
                nueva_opcion = "Hasta que se desactive"
                nueva_duracion_seg = None  # sin expiración fija

            # 🔑 LÓGICA INTELIGENTE: solo renovar si la opción cambió o la expiración ya pasó
            opcion_actual = getattr(conductor, 'opcion_gps', None)
            exp_actual = getattr(conductor, 'expiracion_gps', None)

            # Normalizar exp_actual (si es naive, asumir misma zona horaria)
            if exp_actual and exp_actual.tzinfo is None:
                from utils.time import TZ_CARACAS
                exp_actual = exp_actual.replace(tzinfo=TZ_CARACAS)

            expirada = (exp_actual is None) or (exp_actual < ahora)

            if nueva_opcion != opcion_actual or expirada:
                # Cambió la opción o expiró: renovamos
                if nueva_duracion_seg:
                    conductor.expiracion_gps = ahora + timedelta(seconds=nueva_duracion_seg)
                else:
                    conductor.expiracion_gps = ahora + timedelta(days=365)  # modo indefinido
                conductor.opcion_gps = nueva_opcion
                print(f"🔄 [GPS] {conductor.codigo} renovó expiración: {conductor.expiracion_gps} (opción: {nueva_opcion})")
                # 🟢 SALUDO EXCLUSIVO AL INICIAR O CAMBIAR OPCIÓN DE GPS
                #nombre_conductor = getattr(conductor, 'nombre', None) or conductor.codigo
                #saludo = (
                #    f"👋 ¡Hola, *{nombre_conductor}*!\n\n"
                #    "🚗 Ubicación recibida y conectada con éxito.\n"
                #    "⏱️ Tu turno está activo. ¡Que tengas un excelente recorrido y mucho éxito hoy!"
                #)
                #enviar_mensaje(chat_id, saludo)
            else:
                # Misma opción y aún válida: solo actualizamos coordenadas y timestamp
                print(f"📌 [GPS] {conductor.codigo} actualizó ubicación sin renovar expiración")
                # No tocamos expiracion_gps ni opcion_gps

            # Sincronizar con el turno activo (si existe)
            if hasattr(conductor, "turno_activo") and conductor.turno_activo:
                conductor.turno_activo.expiracion_gps = conductor.expiracion_gps
                conductor.turno_activo.opcion_gps = conductor.opcion_gps

            db.session.commit()
            
            # 📡 EMITIR AL MAPA EN TIEMPO REAL VÍA WEBSOCKET
            emitir_al_panel('nueva_ubicacion', {
                'conductor_id': conductor.id_conductor,
                'codigo': conductor.codigo,
                'nombre': getattr(conductor, 'nombre', 'Conductor'),
                'lat': conductor.latitud,
                'lon': conductor.longitud,
                'ultima_actualizacion': ahora.isoformat()
            })
            return jsonify({"status": "loc_actualizada"}), 200

        # 🛡️ CIERRE SEGURO Y SILENCIOSO: 
        # Si llega cualquier otra actualización que no sea texto ni ubicación activa.
        return jsonify({"status": "actualizacion_silenciada"}), 200

    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN WEBHOOK: {e}")
        import traceback
        traceback.print_exc()
        try:
            return jsonify({"status": "error", "detalle": str(e)}), 200
        except:
            return "OK", 200  # Última red de seguridad: texto plano con código 200 si todo lo demás falla
    
        
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

def enviar_mensaje_con_teclado_inline(chat_id, texto, teclado_json, parse_mode='HTML'):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': parse_mode,
        'reply_markup': json.dumps(teclado_json)
    }
    requests.post(url, data=payload)    

