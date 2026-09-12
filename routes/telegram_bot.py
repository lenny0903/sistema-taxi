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
from extensions import socketio
import time
load_dotenv()
telegram_bp = Blueprint('telegram_bp', __name__)

usuarios_reportando = {}
ULTIMOS_AVISOS_SIN_TURNO = {}
def emitir_al_panel(evento, datos=None):
    try:
        # 🟢 Usar la instancia de socketio importada de extensions
        socketio.emit(evento, datos, namespace='/')
        print(f"✅ Evento '{evento}' emitido con éxito usando socketio.emit")
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

        # =========================================================================
        # 0. PROCESAMIENTO DE BOTONES INLINE (CALLBACK QUERIES)
        # =========================================================================
        callback = update.get('callback_query')
        if callback:
            data = callback.get('data') # Ej: 'cal_123_5'
            chat_id = str(callback['from']['id'])
            callback_id = callback['id']

            # Botón: "Ver mi viaje en curso"
            if data == 'menu_ver_viaje':
                confirmar_clic(callback_id)
                despacho_reciente = Despacho.query.filter_by(
                    telegram_id_cliente=chat_id
                ).order_by(Despacho.id_despacho.desc()).first()
                
                if despacho_reciente:
                    url_mapa = url_for('views.pagina_mapa_despacho', id_despacho=despacho_reciente.id_despacho, _external=True, _scheme='https')
                    print(f"🗺️ [MAPA DEBUG] URL generada para el mapa: {url_mapa}")  # <-- Añade este print
                    teclado_mapa = {
                        "inline_keyboard": [
                            [{"text": "🗺️ Abrir Mapa en Vivo", "url": url_mapa}]
                        ]
                    }
                    enviar_mensaje_con_teclado_inline(
                        chat_id, 
                        f"📍 Aquí tienes el acceso directo al rastreo de tu servicio activo (Despacho #{despacho_reciente.id_despacho}):", 
                        teclado_mapa
                    )
                else:
                    enviar_mensaje(chat_id, "⚠️ No encontramos ningún servicio activo vinculado a tu cuenta en este momento.")
                return jsonify({"status": "menu_viaje_procesado"}), 200

            # Botón: "Ayuda / Soporte"
            if data == 'menu_ayuda':
                confirmar_clic(callback_id)
                enviar_mensaje(
                    chat_id, 
                    "ℹ️ *Centro de Soporte*\n\n"
                    "Si tienes algún inconveniente con tu servicio, puedes escribirnos directamente por este chat o reportarlo al finalizar tu viaje con la calificación de 1 estrella."
                )
                return jsonify({"status": "menu_ayuda_procesado"}), 200

            # Encuesta / Calificación
            if data and data.startswith('cal_'):
                try:
                    _, id_despacho_str, calificacion_str = data.split('_')
                    id_despacho = int(id_despacho_str)
                    estrellas = int(calificacion_str)

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

                confirmar_clic(callback_id)
                
                if estrellas == 1:
                    usuarios_reportando[chat_id] = id_despacho
                    enviar_mensaje(
                        chat_id, 
                        "⚠️ Lamentamos mucho el inconveniente. Por favor, **escribe en un breve mensaje qué sucedió** "
                        "para reportarlo de inmediato con la administración."
                    )
                    return jsonify({"status": "esperando_comentario_inconveniente"}), 200
                else:
                    enviar_mensaje(chat_id, "✅ ¡Muchas gracias por tu opinión! Nos ayuda a mejorar el servicio.")
                    return jsonify({"status": "encuesta_recibida"}), 200

        # =========================================================================
        # 1. IDENTIFICAR EL MENSAJE
        # =========================================================================
        msg = update.get('message') or update.get('edited_message')
        if not msg:
            return jsonify({"status": "sin_mensaje"}), 200

        user_from = msg.get('from')
        if not user_from or 'id' not in user_from:
            return jsonify({"status": "sin_remitente_valido"}), 200
        chat_id = str(user_from['id'])

        # =========================================================================
        # 2. PROCESAMIENTO DE TEXTO
        # =========================================================================
        if 'text' in msg:
            texto = msg['text'].strip()
            
            # Actualizar latido/red si quien escribe es conductor
            conductor_activo_check = Conductor.query.filter_by(telegram_id=chat_id).first()
            if conductor_activo_check:
                conductor_activo_check.ultima_actualizacion_red = hora_local().replace(microsecond=0)
                db.session.commit()

            # Módulo de comentario tras calificación negativa
            if chat_id in usuarios_reportando:
                id_despacho = usuarios_reportando.pop(chat_id)
                try:
                    despacho = Despacho.query.get(id_despacho)
                    if despacho:
                        despacho.comentario_calificacion = texto
                        db.session.commit()
                        print(f"📝 [REPORTE] Comentario guardado para Despacho #{id_despacho}: {texto}")
                    else:
                        print(f"⚠️ [REPORTE] Despacho #{id_despacho} no encontrado.")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Error al guardar comentario de inconveniente: {e}")

                enviar_mensaje(chat_id, "✅ Reporte recibido. Muchas gracias por ayudarnos a mejorar. ¡Feliz día!")
                return jsonify({"status": "comentario_inconveniente_guardado"}), 200

            # --- COMANDO /START ---
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
                            
                            url_mapa = url_for('views.pagina_mapa_despacho', id_despacho=id_despacho, _external=True, _scheme='https')
                            print(f"🗺️ [MAPA DEBUG] URL generada para el mapa: {url_mapa}")  # <-- Añade este print
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
                    if conductor_activo_check:
                        conductor_activo_check.estado_red = 'conectado'
                        if hasattr(conductor_activo_check, 'ultima_actualizacion_red'):
                            conductor_activo_check.ultima_actualizacion_red = hora_local() 
                        db.session.commit()
                        
                        try:
                            from app import socketio
                            socketio.emit('estado_red_cambiado', namespace='/')
                        except Exception as e:
                            print(f"⚠️ No se pudo emitir por socket: {e}")
                        
                        enviar_menu_botones(chat_id)
                    else:
                        teclado_cliente_menu = {
                            "inline_keyboard": [
                                [{"text": "📍 Ver mi viaje en curso", "callback_data": "menu_ver_viaje"}],
                                [{"text": "ℹ️ Ayuda / Soporte", "callback_data": "menu_ayuda"}]
                            ]
                        }
                        enviar_mensaje_con_teclado_inline(
                            chat_id, 
                            "¡Hola! Bienvenido a nuestro servicio de transporte 🚗\n\nSelecciona una opción:", 
                            teclado_cliente_menu
                        )

                    return jsonify({"status": "menu_enviado"}), 200

            # --- PALABRA CLAVE "UBI" (Para Clientes) ---
            if texto.lower() == "ubi":
                print(f"🎯 [WEBHOOK] Petición 'UBI' recibida del chat: {chat_id}")
                
                # Buscar el último despacho asociado a este telegram_id de cliente
                despacho_reciente = Despacho.query.filter_by(telegram_id_cliente=chat_id).order_by(Despacho.id_despacho.desc()).first()
                
                if not despacho_reciente:
                    despacho_reciente = Despacho.query.order_by(Despacho.id_despacho.desc()).first()
                    if despacho_reciente:
                        despacho_reciente.telegram_id_cliente = chat_id
                        db.session.commit()

                if despacho_reciente:
                    conductor_asig = db.session.get(Conductor, despacho_reciente.conductor_id) if hasattr(despacho_reciente, 'conductor_id') and despacho_reciente.conductor_id else None
                    nro_ctrl = conductor_asig.codigo if conductor_asig else "Unidad"
                    nombre_cond = conductor_asig.nombre if conductor_asig else "Conductor"
                    
                    # 👇 CAMBIO AQUÍ: despacho_reciente.id_despacho (no id_despacho)
                    url_mapa = url_for('views.pagina_mapa_despacho', id_despacho=despacho_reciente.id_despacho, _external=True, _scheme='https')
                    
                    teclado_mapa = {
                        "inline_keyboard": [
                            [{"text": "🗺️ Ver Mapa en Tiempo Real", "url": url_mapa}]
                        ]
                    }
                    mensaje_ubi = (
                        f"📍 *Rastreo de tu servicio activo (Despacho #{despacho_reciente.id_despacho})*\n\n"
                        f"🚗 Unidad: #{nro_ctrl}\n"
                        f"👤 Conductor: {nombre_cond}\n\n"
                        "Haz clic en el botón de abajo para seguir la unidad en vivo:"
                    )
                    enviar_mensaje_con_teclado_inline(chat_id, mensaje_ubi, teclado_mapa)
                else:
                    enviar_mensaje(chat_id, "⚠️ No tienes ningún servicio activo registrado en este momento.")
                
                return jsonify({"status": "ubi_procesado"}), 200

            # --- BOTÓN ACTIVAR (Conductores) ---
            if texto == "🔗 Activar":
                if conductor_activo_check:
                    enviar_mensaje(chat_id, "✅ Ya estás vinculado al sistema.")
                else:
                    enviar_mensaje(chat_id, "🆔 Por favor, escribe tu código (ejemplo: B64) para activar tu cuenta.")
                enviar_menu_botones(chat_id)
                return jsonify({"status": "esperando_codigo"}), 200

            # --- VALIDACIÓN DE CÓDIGO (Conductores) ---
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

            # Si es un texto libre de un conductor, muestra el menú de botones
            if conductor_activo_check:
                enviar_menu_botones(chat_id)
            else:
                # Si es un cliente escribiendo cualquier texto libre
                teclado_cliente_menu = {
                    "inline_keyboard": [
                        [{"text": "📍 Ver mi viaje en curso", "callback_data": "menu_ver_viaje"}],
                        [{"text": "ℹ️ Ayuda / Soporte", "callback_data": "menu_ayuda"}]
                    ]
                }
                enviar_mensaje_con_teclado_inline(
                    chat_id, 
                    "¡Hola! Escribe *ubi* o utiliza las opciones del menú:", 
                    teclado_cliente_menu
                )

            return jsonify({"status": "texto_procesado"}), 200

        # =========================================================================
        # 3. VERIFICAR SI EL REMITENTE ES CONDUCTOR PARA GPS
        # =========================================================================
        conductor = Conductor.query.filter_by(telegram_id=chat_id).first()

        if not conductor:
            if "location" in msg:
                return jsonify({"status": "ubicacion_ignorada_sin_registro"}), 200

            teclado_cliente_menu = {
                "inline_keyboard": [
                    [{"text": "📍 Ver mi viaje en curso", "callback_data": "menu_ver_viaje"}],
                    [{"text": "ℹ️ Ayuda / Soporte", "callback_data": "menu_ayuda"}]
                ]
            }
            enviar_mensaje_con_teclado_inline(
                chat_id, 
                "Bienvenido 🚗. Escribe *ubi* para obtener el mapa de tu viaje:", 
                teclado_cliente_menu
            )
            return jsonify({"status": "cliente_atendido"}), 200

        # =========================================================================
        # 4. PROCESAMIENTO DE UBICACIÓN (LIVE LOCATION Y EXPIRED)
        # =========================================================================
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
            
            emitir_al_panel('conductor_inactivo', {
                'conductor_id': conductor.id_conductor,
                'codigo': conductor.codigo
            })
            
            enviar_mensaje(chat_id, "🛑 Has dejado de compartir tu ubicación. Sesión de GPS finalizada correctamente.")
            enviar_menu_botones(chat_id)
            print(f"🛑 [GPS] El conductor {conductor.codigo} finalizó su GPS manualmente.")
            return jsonify({"status": "loc_finalizada_manual"}), 200

        if "location" in msg:
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

            ahora = hora_local().replace(microsecond=0)

            conductor.latitud = msg["location"]["latitude"]
            conductor.longitud = msg["location"]["longitude"]
            conductor.ultima_actualizacion = ahora
            conductor.aviso_enviado = 0
            
            if hasattr(conductor, 'estado_red'):
                conductor.estado_red = 'conectado'
            if hasattr(conductor, 'ultima_actualizacion_red'):
                conductor.ultima_actualizacion_red = ahora

            conductor.alerta_enviada = False

            segundos = msg["location"].get("live_period")

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
                nueva_duracion_seg = None

            opcion_actual = getattr(conductor, 'opcion_gps', None)
            exp_actual = getattr(conductor, 'expiracion_gps', None)

            if exp_actual and exp_actual.tzinfo is None:
                from utils.time import TZ_CARACAS
                exp_actual = exp_actual.replace(tzinfo=TZ_CARACAS)

            expirada = (exp_actual is None) or (exp_actual < ahora)

            if nueva_opcion != opcion_actual or expirada:
                if nueva_duracion_seg:
                    conductor.expiracion_gps = ahora + timedelta(seconds=nueva_duracion_seg)
                else:
                    conductor.expiracion_gps = ahora + timedelta(days=365)
                conductor.opcion_gps = nueva_opcion
                print(f"🔄 [GPS] {conductor.codigo} renovó expiración: {conductor.expiracion_gps} (opción: {nueva_opcion})")
            else:
                print(f"📌 [GPS] {conductor.codigo} actualizó ubicación sin renovar expiración")

            if hasattr(conductor, "turno_activo") and conductor.turno_activo:
                conductor.turno_activo.expiracion_gps = conductor.expiracion_gps
                conductor.turno_activo.opcion_gps = conductor.opcion_gps

            db.session.commit()
            
            emitir_al_panel('nueva_ubicacion', {
                'conductor_id': conductor.id_conductor,
                'codigo': conductor.codigo,
                'nombre': getattr(conductor, 'nombre', 'Conductor'),
                'lat': conductor.latitud,
                'lon': conductor.longitud,
                'ultima_actualizacion': ahora.isoformat()
            })
            return jsonify({"status": "loc_actualizada"}), 200

        return jsonify({"status": "actualizacion_silenciada"}), 200

    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN WEBHOOK: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "detalle": str(e)}), 200        
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

from models.conductores import Conductor

def enviar_menu_botones(chat_id):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # 1. Verificamos si este chat_id pertenece a un conductor registrado
    conductor = Conductor.query.filter_by(telegram_id=str(chat_id)).first()
    
    if conductor:
        # 🚗 CONFIGURACIÓN PARA CONDUCTORES (Mantiene su botón de activación)
        teclado = {
            "keyboard": [
                [{"text": "🔗 Activar"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        texto_mensaje = "✅ Sistema de Rastreo Activo. Presiona el botón inferior si necesitas vincular tu cuenta:"
    else:
        # 👤 CONFIGURACIÓN PARA CLIENTES (Sin botones extraños, chat limpio para que puedan escribir comentarios)
        teclado = {
            "remove_keyboard": True
        }
        texto_mensaje = "¡Hola! Bienvenido al seguimiento de tu servicio. Puedes escribir tus comentarios o consultas directamente por aquí:"

    payload = {
        'chat_id': chat_id,
        'text': texto_mensaje,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(teclado) 
    }
    
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"⚠️ Error enviando menú de botones: {e}")

def limpiar_teclado_conductor(chat_id):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': "⚙️ Actualizando configuración...",
        'reply_markup': json.dumps({"remove_keyboard": True})
    }
    requests.post(url, data=payload)

from utils.notificaciones import _enviar_peticion
def enviar_mensaje_con_teclado_inline(chat_id, texto, teclado_json, parse_mode='Markdown'):
    """Envía mensajes con botones inline flotantes (mapas, enlaces, etc.)."""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN no está definido en el entorno")
        return {"ok": False, "error": "Token no definido"}
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Pasamos el diccionario directamente sin json.dumps previo
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': parse_mode,
        'reply_markup': teclado_json  
    }
    
    print(f"📤 Enviando mensaje con botón inline a {chat_id}...")
    # CAMBIAMOS A True para enviar un JSON limpio que Telegram no rechace
    resultado = _enviar_peticion(url, payload, es_json=True)
    print(f"📤 Respuesta de Telegram: {resultado}")
    return resultado

def publicar_en_canal(id_despacho):
    from models.despachos import Despacho
    from models.conductores import Conductor
    from utils.notificaciones import enviar_mensaje_con_teclado_inline

    despacho = Despacho.query.get(id_despacho)
    if not despacho:
        print(f"⚠️ Despacho #{id_despacho} no encontrado.")
        return

    conductor = Conductor.query.get(despacho.conductor_id) if despacho.conductor_id else None
    nro_ctrl = conductor.codigo if conductor else "Unidad"
    nombre_cond = conductor.nombre if conductor else "Conductor"

    # 🚀 Bot de PRODUCCIÓN
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

    # 🚀 Canal de PRODUCCIÓN
    canal_chat_id = "@Lospatriotasdetariba"

    enviar_mensaje_con_teclado_inline(canal_chat_id, mensaje, teclado)
    print(f"📢 Mensaje publicado en el canal para el Despacho #{id_despacho}")