import os
import sys
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Verificar token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("❌ Token no encontrado en .env")
    sys.exit(1)

print(f"✅ Token cargado: {TOKEN[:5]}...")

# Definir el mensaje y teclado
chat_id = "@taxi_tariberosLosPatriotas"
texto = "Mensaje de prueba desde script"
teclado = {
    "inline_keyboard": [
        [{"text": "🚗 Ver mi viaje", "url": "https://t.me/taxi_tariberosLosPatriotas?start=srv-123"}]
    ]
}

# Enviar mensaje
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    'chat_id': chat_id,
    'text': texto,
    'parse_mode': 'HTML',
    'reply_markup': json.dumps(teclado)
}

print(f"📤 Enviando a {chat_id}...")
response = requests.post(url, data=payload)
print(f"📤 Código de estado: {response.status_code}")
print(f"📤 Respuesta de Telegram: {response.text}")