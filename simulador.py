import requests
import time
import random

# Lista de códigos de conductores que queremos simular
conductores_a_simular = ["B60", "B10", "B15"] 
url_api = "http://127.0.0.1:5000/conductores/actualizar_ubicacion"

def simular_movimiento():
    print("Iniciando simulación de flota... (Presiona Ctrl+C para detener)")
    while True:
        for codigo in conductores_a_simular:
            # Generamos un movimiento pequeño y aleatorio cerca de San Cristóbal
            lat = 7.760 + random.uniform(-0.01, 0.01)
            lon = -72.220 + random.uniform(-0.01, 0.01)
            
            data = {"codigo": codigo, "latitud": lat, "longitud": lon}
            
            try:
                response = requests.post(url_api, json=data)
                if response.status_code == 200:
                    print(f"Unidad {codigo} movida a: {lat:.4f}, {lon:.4f}")
                else:
                    print(f"Error al mover {codigo}: {response.text}")
            except Exception as e:
                print(f"Error de conexión: {e}")
        
        # Esperamos 10 segundos antes de la siguiente actualización
        time.sleep(10)

if __name__ == "__main__":
    simular_movimiento()