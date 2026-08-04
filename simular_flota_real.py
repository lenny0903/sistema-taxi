import requests
import time
import random

# URL de tu servidor local en la laptop
BASE_URL = "http://127.0.0.1:5000"

# Tus códigos reales extraídos directamente de la base de datos
CODIGOS_REALES = [
    "B07", "B10", "B15", "B16", "B18", 
    "B19", "B20", "B21", "B22", "B23", 
    "B24", "B25", "B26", "B27"
]

def simular_envio_gps(codigo, latitud, longitud):
    url = f"{BASE_URL}/conductores/actualizar_ubicacion"
    payload = {
        "codigo": codigo,
        "latitud": latitud,
        "longitud": longitud
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"📡 Conductor {codigo} -> Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error al conectar para {codigo}: {e}")

if __name__ == "__main__":
    print("--- INICIANDO SIMULADOR CON FLOTA REAL ---")
    
    # Coordenadas base en San Cristóbal
    lat_centro = 7.7661
    lon_centro = -72.2230

    # Ejecutaremos 5 rondas de prueba
    for ronda in range(1, 50):
        print(f"\n--- Ronda de actualización #{ronda} ---")
        
        for codigo in CODIGOS_REALES:
            # Variación leve de coordenadas para simular movimiento en mapa
            lat_aleatoria = lat_centro + random.uniform(-0.015, 0.015)
            lon_aleatoria = lon_centro + random.uniform(-0.015, 0.015)
            
            simular_envio_gps(codigo, lat_aleatoria, lon_aleatoria)
        
        time.sleep(5)
    
    print("\n--- SIMULACIÓN FINALIZADA ---")