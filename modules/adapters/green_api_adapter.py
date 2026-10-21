import os
import requests

GREEN_API_INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID", "")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN", "")
GREEN_API_URL = f"https://api.green-api.com/waInstance{GREEN_API_INSTANCE_ID}"

def parse_green_api_payload(data):
    """
    Traduce el JSON de Green-API al diccionario estándar del sistema.
    """
    try:
        type_webhook = data.get("typeWebhook")
        if type_webhook != "incomingMessageReceived":
            return None

        message_data = data.get("messageData", {})
        sender_data = data.get("senderData", {})
        
        telefono = sender_data.get("sender", "").replace("@c.us", "")
        chat_id = sender_data.get("chatId")
        nombre = sender_data.get("senderName", "Cliente GreenAPI")
        type_message = message_data.get("typeMessage")

        evento = {
            "chat_id": chat_id,
            "telefono": telefono,
            "nombre": nombre,
            "tipo_msg": type_message,
            "texto": "",
            "lat": None,
            "lng": None
        }

        if type_message in ["textMessage", "extendedTextMessage"]:
            evento["texto"] = message_data.get("textMessageData", {}).get("textMessage", "").strip().lower()
        elif type_message == "locationMessage":
            loc = message_data.get("locationMessageData", {})
            evento["lat"] = loc.get("latitude")
            evento["lng"] = loc.get("longitude")

        return evento
    except Exception as e:
        print(f"[Error Parse Green-API Payload]: {e}")
        return None

def send_green_api_message(chat_id, texto):
    """
    Envía mensajes de texto usando Green-API.
    """
    url = f"{GREEN_API_URL}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": texto
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"[Error Green-API Enviar Mensaje]: {e}")
        return False