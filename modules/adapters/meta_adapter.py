import os
import requests

META_TOKEN = os.getenv("META_ACCESS_TOKEN", "tu_token_sandbox_meta")
PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "tu_phone_id")
META_API_VERSION = "v18.0"

def parse_meta_payload(data):
    """
    Traduce el JSON de Meta Cloud API a un diccionario estándar del sistema.
    """
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        msg = messages[0]
        contacts = value.get("contacts", [{}])[0]
        
        telefono = msg.get("from") # Ej: 584121234567
        chat_id = telefono
        nombre = contacts.get("profile", {}).get("name", "Cliente Meta")
        msg_type = msg.get("type") # text, location, etc.
        
        # Estructura normalizada universal
        evento = {
            "chat_id": chat_id,
            "telefono": telefono,
            "nombre": nombre,
            "tipo_msg": "",
            "texto": "",
            "lat": None,
            "lng": None
        }

        if msg_type == "text":
            evento["tipo_msg"] = "textMessage"
            evento["texto"] = msg.get("text", {}).get("body", "").strip().lower()
        elif msg_type == "location":
            evento["tipo_msg"] = "locationMessage"
            loc = msg.get("location", {})
            evento["lat"] = loc.get("latitude")
            evento["lng"] = loc.get("longitude")

        return evento
    except Exception as e:
        print(f"[Error Parse Meta Payload]: {e}")
        return None

def send_meta_message(chat_id, texto):
    """
    Envía mensajes de texto usando la Cloud API oficial de Meta.
    """
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": chat_id,
        "type": "text",
        "text": {"body": texto}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[Error Meta Enviar Mensaje]: {e}")
        return False