import requests

def enviar_ping_telegram(chat_id, token_bot):
    """Envía un ping de acción (typing) para intentar despertar el socket del teléfono."""
    url = f"https://api.telegram.org/bot{token_bot}/sendChatAction"
    payload = {
        "chat_id": chat_id,
        "action": "typing"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error al enviar sendChatAction al chat {chat_id}: {e}")
        return False