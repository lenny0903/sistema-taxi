import os
import requests
from datetime import datetime, timedelta
from flask import url_for
from extensions import db, socketio
from models.despachos import Despacho
from models.conductores import Conductor
from utils.time import hora_local
from utils.notificaciones import enviar_mensaje, enviar_menu_botones, enviar_mensaje_con_teclado_inline, _enviar_peticion

# Diccionarios de estado en memoria
usuarios_reportando = {}

def emitir_al_panel(evento, datos=None):
    try:
        socketio.emit(evento, datos, namespace='/')
        print(f"✅ Evento '{evento}' emitido con éxito usando socketio.emit")
    except Exception as e:
        print(f"❌ Error al emitir evento: {e}")

def confirmar_clic(callback_id):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    requests.post(url, data={'callback_query_id': callback_id})

def procesar_update_telegram(update):
    """Encargado de enrutar si es un callback (botón inline), un texto o una ubicación."""
    msg = update.get('message') or update.get('edited_message')
    if not msg:
        return {"status": "sin_mensaje"}, 200

    user_from = msg.get('from')
    chat_id = str(user_from['id'])

    # NUEVO: Si el usuario compartió su contacto mediante el botón
    if 'contact' in msg:
        return _manejar_contacto(chat_id, msg['contact'])

    if 'text' in msg:
        return _manejar_texto(chat_id, msg['text'].strip())
    # 0. BOTONES INLINE (CALLBACK QUERIES)
    callback = update.get('callback_query')
    if callback:
        return _manejar_callback(callback)

    # 1. IDENTIFICAR EL MENSAJE
    msg = update.get('message') or update.get('edited_message')
    if not msg:
        return {"status": "sin_mensaje"}, 200

    user_from = msg.get('from')
    if not user_from or 'id' not in user_from:
        return {"status": "sin_remitente_valido"}, 200
    
    chat_id = str(user_from['id'])

    # 2. PROCESAMIENTO DE TEXTO
    if 'text' in msg:
        return _manejar_texto(chat_id, msg['text'].strip())

    # 3. PROCESAMIENTO DE UBICACIÓN (GPS)
    if 'location' in msg:
        return _manejar_ubicacion(chat_id, msg, update)

    return {"status": "actualizacion_silenciada"}, 200


def _manejar_callback(callback):
    data = callback.get('data')
    chat_id = str(callback['from']['id'])
    callback_id = callback['id']

    if data == 'menu_ver_viaje':
        confirmar_clic(callback_id)
        despacho_reciente = Despacho.query.filter_by(telegram_id_cliente=chat_id).order_by(Despacho.id_despacho.desc()).first()
        
        if despacho_reciente:
            url_mapa = url_for('views.pagina_mapa_despacho', id_despacho=despacho_reciente.id_despacho, _external=True, _scheme='https')
            teclado_mapa = {"inline_keyboard": [[{"text": "🗺️ Abrir Mapa en Vivo", "url": url_mapa}]]}
            enviar_mensaje_con_teclado_inline(chat_id, f"📍 Rastreo de tu servicio activo (Despacho #{despacho_reciente.id_despacho}):", teclado_mapa)
        else:
            enviar_mensaje(chat_id, "⚠️ No encontramos ningún servicio activo vinculado a tu cuenta.")
        return {"status": "menu_viaje_procesado"}, 200

    if data == 'menu_ayuda':
        confirmar_clic(callback_id)
        enviar_mensaje(chat_id, "ℹ️ *Centro de Soporte*\n\nSi tienes inconvenientes, repórtalo al finalizar tu viaje.")
        return {"status": "menu_ayuda_procesado"}, 200

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
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al guardar calificación: {e}")

        confirmar_clic(callback_id)
        
        if estrellas == 1:
            usuarios_reportando[chat_id] = id_despacho
            enviar_mensaje(chat_id, "⚠️ Por favor, **escribe brevemente qué sucedió** para reportarlo.")
            return {"status": "esperando_comentario_inconveniente"}, 200
        else:
            enviar_mensaje(chat_id, "✅ ¡Muchas gracias por tu opinión!")
            return {"status": "encuesta_recibida"}, 200

    return {"status": "callback_no_reconocido"}, 200


def _manejar_texto(chat_id, texto):
    conductor_activo = Conductor.query.filter_by(telegram_id=chat_id).first()
    if conductor_activo:
        conductor_activo.ultima_actualizacion_red = hora_local().replace(microsecond=0)
        db.session.commit()

    # Comentario tras calificación negativa
    if chat_id in usuarios_reportando:
        id_despacho = usuarios_reportando.pop(chat_id)
        try:
            despacho = Despacho.query.get(id_despacho)
            if despacho:
                despacho.comentario_calificacion = texto
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al guardar comentario: {e}")

        enviar_mensaje(chat_id, "✅ Reporte recibido. ¡Muchas gracias y feliz día!")
        return {"status": "comentario_guardado"}, 200

    # Comando /START
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
                    
                    conductor_asig = db.session.get(Conductor, despacho.conductor_id) if getattr(despacho, 'conductor_id', None) else None
                    nro_ctrl = conductor_asig.codigo if conductor_asig else "Unidad"
                    nombre_cond = conductor_asig.nombre if conductor_asig else "Conductor"
                    
                    url_mapa = url_for('views.pagina_mapa_despacho', id_despacho=id_despacho, _external=True, _scheme='https')
                    teclado_cliente = {"inline_keyboard": [[{"text": "🗺️ Ver Mapa en Tiempo Real", "url": url_mapa}]]}
                    mensaje = f"📍 *Rastreo de servicio #{id_despacho}*\n🚗 Unidad: #{nro_ctrl}\n👤 Conductor: {nombre_cond}"
                    enviar_mensaje_con_teclado_inline(chat_id, mensaje, teclado_cliente)
                else:
                    enviar_mensaje(chat_id, "⚠️ No encontramos los datos de este servicio.")
            except Exception as e:
                print(f"❌ Error en start cliente: {e}")
            return {"status": "menu_client_enviado"}, 200
        else:
            if conductor_activo:
                conductor_activo.estado_red = 'conectado'
                db.session.commit()
                emitir_al_panel('estado_red_cambiado')
                enviar_menu_botones(chat_id)
            else:
                teclado_menu = {
                    "inline_keyboard": [
                        [{"text": "📍 Ver mi viaje en curso", "callback_data": "menu_ver_viaje"}],
                        [{"text": "ℹ️ Ayuda / Soporte", "callback_data": "menu_ayuda"}]
                    ]
                }
                enviar_mensaje_con_teclado_inline(chat_id, "¡Bienvenido a nuestro servicio 🚗! Selecciona una opción:", teclado_menu)
            return {"status": "menu_enviado"}, 200

    # Palabra clave UBI
    if texto.lower() == "ubi":
        despacho_reciente = Despacho.query.filter_by(telegram_id_cliente=chat_id).order_by(Despacho.id_despacho.desc()).first()
        if not despacho_reciente:
            despacho_reciente = Despacho.query.order_by(Despacho.id_despacho.desc()).first()
            if despacho_reciente:
                despacho_reciente.telegram_id_cliente = chat_id
                db.session.commit()

        if despacho_reciente:
            conductor_asig = db.session.get(Conductor, despacho_reciente.conductor_id) if getattr(despacho_reciente, 'conductor_id', None) else None
            nro_ctrl = conductor_asig.codigo if conductor_asig else "Unidad"
            nombre_cond = conductor_asig.nombre if conductor_asig else "Conductor"
            url_mapa = url_for('views.pagina_mapa_despacho', id_despacho=despacho_reciente.id_despacho, _external=True, _scheme='https')
            
            teclado_mapa = {"inline_keyboard": [[{"text": "🗺️ Ver Mapa en Tiempo Real", "url": url_mapa}]]}
            enviar_mensaje_con_teclado_inline(chat_id, f"📍 *Rastreo Despacho #{despacho_reciente.id_despacho}*\n🚗 Unidad: #{nro_ctrl}", teclado_mapa)
        else:
            enviar_mensaje(chat_id, "⚠️ No tienes ningún servicio activo registrado.")
        return {"status": "ubi_procesado"}, 200

    # Activar Conductor
    if texto == "🔗 Activar":
        if conductor_activo:
            enviar_mensaje(chat_id, "✅ Ya estás vinculado al sistema.")
        else:
            enviar_mensaje(chat_id, "🆔 Escribe tu código (ejemplo: B64) para activar tu cuenta.")
        enviar_menu_botones(chat_id)
        return {"status": "esperando_codigo"}, 200

    # Validación de Código Bxx (Paso 1: Solicitar contacto para verificar)
    if texto.upper().startswith('B') and len(texto) >= 2:
        conductor_c = Conductor.query.filter_by(codigo=texto.upper()).first()
        if conductor_c:
            # Guardamos temporalmente en memoria qué conductor quiere activar este chat_id
            usuarios_reportando[chat_id] = f"activando_{conductor_c.id_conductor}"
            
            # Creamos un botón nativo de Telegram para compartir contacto
            teclado_contacto = {
                "keyboard": [[{"text": "📱 Compartir mi número de teléfono", "request_contact": True}]],
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
            # Usas tu función de envío con teclado normal (no inline)
            from utils.notificaciones import _enviar_peticion
            _enviar_peticion("sendMessage", {
                "chat_id": chat_id,
                "text": f"⚠️ Para vincular la unidad {conductor_c.codigo}, por favor comparte tu número de teléfono oficial usando el botón de abajo:",
                "reply_markup": teclado_contacto
            })
        else:
            enviar_mensaje(chat_id, "🚫 Código no encontrado.")
        return {"status": "esperando_contacto_verificacion"}, 200

    if conductor_activo:
        enviar_menu_botones(chat_id)
    else:
        teclado_menu = {
            "inline_keyboard": [
                [{"text": "📍 Ver mi viaje en curso", "callback_data": "menu_ver_viaje"}],
                [{"text": "ℹ️ Ayuda / Soporte", "callback_data": "menu_ayuda"}]
            ]
        }
        enviar_mensaje_con_teclado_inline(chat_id, "Escribe *ubi* o utiliza las opciones del menú:", teclado_menu)

    return {"status": "texto_procesado"}, 200


def _manejar_ubicacion(chat_id, msg, update):
    conductor = Conductor.query.filter_by(telegram_id=chat_id).first()
    if not conductor:
        return {"status": "ubicacion_ignorada_sin_registro"}, 200

    es_cierre_manual = "edited_message" in update and "live_period" not in msg["location"]
    if es_cierre_manual:
        ahora = hora_local()
        conductor.expiracion_gps = ahora
        conductor.opcion_gps = "Finalizado"
        if hasattr(conductor, "turno_activo") and conductor.turno_activo:
            conductor.turno_activo.expiracion_gps = ahora
            conductor.turno_activo.opcion_gps = "Finalizado"
        db.session.commit()
        
        emitir_al_panel('conductor_inactivo', {'conductor_id': conductor.id_conductor, 'codigo': conductor.codigo})
        enviar_mensaje(chat_id, "🛑 Sesión de GPS finalizada correctamente.")
        enviar_menu_botones(chat_id)
        return {"status": "loc_finalizada_manual"}, 200

    if "edited_message" not in update and "live_period" not in msg["location"]:
        enviar_mensaje(chat_id, "⚠️ Debes compartir tu **'Ubicación en tiempo real'**.")
        enviar_menu_botones(chat_id)
        return {"status": "ubicacion_estatica_rechazada"}, 200

    ahora = hora_local().replace(microsecond=0)
    conductor.latitud = msg["location"]["latitude"]
    conductor.longitud = msg["location"]["longitude"]
    conductor.ultima_actualizacion = ahora
    conductor.aviso_enviado = 0
    conductor.estado_red = 'conectado'
    conductor.alerta_enviada = False

    segundos = msg["location"].get("live_period")
    nueva_opcion = "15 min" if segundos == 900 else ("1 hora" if segundos == 3600 else ("8 horas" if segundos == 28800 else "Hasta que se desactive"))
    nueva_duracion_seg = segundos if segundos in [900, 3600, 28800] else None

    exp_actual = getattr(conductor, 'expiracion_gps', None)
    if exp_actual and exp_actual.tzinfo is None:
        from utils.time import TZ_CARACAS
        exp_actual = exp_actual.replace(tzinfo=TZ_CARACAS)

    if (exp_actual is None) or (exp_actual < ahora) or (getattr(conductor, 'opcion_gps', None) != nueva_opcion):
        if nueva_duracion_seg:
            conductor.expiracion_gps = ahora + timedelta(seconds=nueva_duracion_seg)
        else:
            conductor.expiracion_gps = ahora + timedelta(days=365)
        conductor.opcion_gps = nueva_opcion

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
    return {"status": "loc_actualizada"}, 200

def _manejar_contacto(chat_id, contact):
    # Verificamos si este chat estaba en proceso de activación
    estado_temp = usuarios_reportando.get(chat_id)
    if not estado_temp or not estado_temp.startswith("activando_"):
        enviar_mensaje(chat_id, "⚠️ No hay ninguna activación pendiente.")
        return {"status": "contacto_sin_proceso"}, 200

    conductor_id = int(estado_temp.split("_")[1])
    conductor = Conductor.query.get(conductor_id)
    
    if not conductor:
        enviar_mensaje(chat_id, "🚫 Conductor no encontrado.")
        return {"status": "conductor_no_encontrado"}, 200

    # Teléfono que envió Telegram (limpiando símbolos)
    telefono_telegram = contact.get('phone_number', '').replace('+', '').strip()
    # Teléfono registrado en tu base de datos
    telefono_bd = str(conductor.telefono).replace('+', '').strip()

    # Validar coincidencia de números
    if telefono_telegram in telefono_bd or telefono_bd in telefono_telegram:
        # ¡Coinciden! Es el teléfono real del titular
        conductor.telegram_id = chat_id
        db.session.commit()
        
        # Limpiar estado temporal
        usuarios_reportando.pop(chat_id, None)
        
        enviar_mensaje(chat_id, f"🎉 ¡Bienvenido {conductor.nombre}! Cuenta activada correctamente.")
        enviar_menu_botones(chat_id)
        return {"status": "vinculacion_exitosa"}, 200
    else:
        # No coinciden: la cuenta de Telegram es de otra persona o número
        usuarios_reportando.pop(chat_id, None)
        enviar_mensaje(chat_id, "❌ **Acceso denegado**: El número de esta cuenta de Telegram no coincide con el teléfono registrado para esta unidad en el sistema.")
        return {"status": "vinculacion_rechazada_por_telefono"}, 200