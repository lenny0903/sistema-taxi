import random
import time
import requests

BASE_URL = "http://127.0.0.1:5000"

# Mapeo de códigos a telegram_ids simulados (o reales de tu DB)
# Asegúrate de que el B10 tenga su telegram_id configurado para que la consulta en el webhook lo reconozca
CONDUCTORES_SIMULADOS = [
    {"codigo": "B19", "telegram_id": "5987075437"},
    {"codigo": "B22", "telegram_id": "8772520835"},
    {"codigo": "B20", "telegram_id": "8723268955"},
]


def simular_envio_telegram(telegram_id, latitud, longitud):
    # 👈 Cambia la URL agregando el prefijo del Blueprint (ej. /telegram/webhook)
    url = f"{BASE_URL}/telegram/webhook" 

    payload = {
        "update_id": 1000001,
        "edited_message": {
            "from": {"id": int(telegram_id), "first_name": "Simulador"},
            "chat": {"id": int(telegram_id), "type": "private"},
            "location": {
                "latitude": latitud,
                "longitude": longitud,
                "live_period": 900,
            },
        },
    }

    try:
        response = requests.post(url, json=payload)
        print(f"📡 Telegram ID {telegram_id} -> Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")

if __name__ == "__main__":
    print("--- SIMULANDO ENVIOS REALES DE TELEGRAM (8 HORAS) ---")
    lat_centro = 7.7661
    lon_centro = -72.2230

    for ronda in range(1, 20):
        print(f"\n--- Ronda #{ronda} ---")
        for cond in CONDUCTORES_SIMULADOS:
            lat_aleatoria = lat_centro + random.uniform(-0.015, 0.015)
            lon_aleatoria = lon_centro + random.uniform(-0.015, 0.015)

            simular_envio_telegram(
                cond["telegram_id"], lat_aleatoria, lon_aleatoria
            )

        time.sleep(5)