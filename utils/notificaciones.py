from flask import request, jsonify
import os
import json
from dotenv import load_dotenv

# 🚀 IMPORTANTE: Usar urllib verde de eventlet (compatible con eventlet.monkey_patch)
from eventlet.green.urllib.request import Request, urlopen
from eventlet.green.urllib.parse import urlencode

load_dotenv()

from models.despachos import Despacho
from extensions import db
from utils.time import hora_local


def _enviar_peticion(url, payload_dict, es_json=False):
    """
    Función auxiliar que envía la petición a Telegram usando urllib verde.
    Evita el error 'maximum recursion depth exceeded' con eventlet.
    """
    try:
        if es_json:
            data = json.dumps(payload_dict).encode('utf-8')
            req = Request(url, data=data)
            req.add_header('Content-Type', 'application/json')
        else:
            data = urlencode(payload_dict).encode('utf-8')
            req = Request(url, data=data)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        response = urlopen(req, timeout=15)
        resultado = json.loads(response.read().decode('utf-8'))
        return resultado
    except Exception as e:
        print(f"❌ Error al enviar petición a Telegram: {e}")
        return {"ok": False, "error": str(e)}


def enviar_mensaje(chat_id, texto, parse_mode='HTML', reply_markup=None):
    """Función centralizada para enviar mensajes sin dependencias circulares."""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': parse_mode
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup if isinstance(reply_markup, str) else json.dumps(reply_markup)
    
    return _enviar_peticion(url, payload, es_json=False)


def enviar_menu_botones(chat_id):
    """Envía el menú inferior básico de activación para conductores."""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
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
    return _enviar_peticion(url, payload, es_json=False)


def enviar_mensaje_con_teclado_inline(chat_id, texto, teclado_json, parse_mode='HTML'):
    """Envía mensajes con botones inline flotantes (mapas, enlaces, etc.)."""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN no está definido en el entorno")
        return {"ok": False, "error": "Token no definido"}
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': parse_mode,
        'reply_markup': json.dumps(teclado_json)
    }
    
    print(f"📤 Enviando mensaje a {chat_id}...")
    resultado = _enviar_peticion(url, payload, es_json=False)
    print(f"📤 Respuesta de Telegram: {resultado}")
    return resultado


def enviar_encuesta_satisfaccion(chat_id_cliente, id_despacho):
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    teclado_encuesta = {
        "inline_keyboard": [
            [{"text": "⭐ Excelente", "callback_data": f"cal_{id_despacho}_5"}],
            [{"text": "⭐ Bueno", "callback_data": f"cal_{id_despacho}_4"}],
            [{"text": "😐 Regular", "callback_data": f"cal_{id_despacho}_3"}],
            [{"text": "⚠️ Inconveniente", "callback_data": f"cal_{id_despacho}_1"}]
        ]
    }
    
    mensaje = (
        "🏁 *¡Has llegado a tu destino!* 🚕✨\n\n"
        "Gracias por confiar en nuestra línea. Nos encantaría conocer tu experiencia:\n"
        "¿Cómo calificarías el servicio recibido hoy?"
    )
    
    payload = {
        'chat_id': chat_id_cliente,
        'text': mensaje,
        'parse_mode': 'Markdown',
        'reply_markup': json.dumps(teclado_encuesta)
    }
    return _enviar_peticion(url, payload, es_json=False)


def procesar_calificacion_cliente(callback_id, chat_id, data):
    """
    Procesa el callback que viene del bot cuando el cliente presiona una estrella.
    Formato esperado del data: 'cal_{id_despacho}_{estrellas}'
    """
    try:
        partes = data.split('_')
        if len(partes) != 3:
            return
            
        _, id_despacho_str, estrellas_str = partes
        id_despacho = int(id_despacho_str)
        estrellas = int(estrellas_str)

        # 1. Buscar el despacho en la base de datos
        despacho = Despacho.query.get(id_despacho)
        
        if despacho:
            # 2. Guardar la calificación y la fecha actual
            despacho.calificacion = estrellas
            despacho.fecha_calificacion = hora_local()
            db.session.commit()
            print(f"⭐ [ENCUESTA] Calificación de {estrellas} estrellas guardada para el despacho #{id_despacho}")
        else:
            print(f"⚠️ [ENCUESTA] No se encontró el despacho #{id_despacho} en la base de datos.")

        # 4. Enviar mensaje de agradecimiento al chat del cliente
        texto_agradecimiento = f"✅ ¡Muchas gracias por tu calificación de {estrellas} estrellas! Nos ayuda a mejorar el servicio. ¡Feliz día! 🚗💨"
        enviar_mensaje(chat_id, texto_agradecimiento)

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al procesar la calificación de la encuesta: {e}")