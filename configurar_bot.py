import os
import re
from dotenv import load_dotenv
load_dotenv()
import requests

def obtener_url_desde_log():
    """Intenta leer la URL del túnel desde el archivo tunnel.log"""
    log_path = "tunnel.log"  # Se guarda en el directorio actual
    try:
        with open(log_path, 'r') as f:
            contenido = f.read()
            # Busca cualquier URL de trycloudflare.com
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', contenido)
            if match:
                return match.group(0)
    except FileNotFoundError:
        pass
    return None

def configurar_webhook():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ No se encontró TELEGRAM_BOT_TOKEN en el archivo .env")
        return

    print("--- Configuración automática de Webhook ---")
    
    # Intentar obtener la URL automáticamente
    url = obtener_url_desde_log()
    if url:
        print(f"🔍 URL detectada automáticamente: {url}")
        confirmar = input("¿Usar esta URL? (s/n): ").strip().lower()
        if confirmar != 's':
            url = input("Ingresa la URL manualmente: ").strip()
    else:
        url = input("Ingresa la URL de tu túnel (ej. https://xxx.trycloudflare.com): ").strip()
    
    # Asegurar el formato
    if not url.endswith('/telegram/webhook'):
        url = url.rstrip('/') + '/telegram/webhook'
    
    api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, data={'url': url})
        resultado = response.json()
        if resultado.get('ok'):
            print(f"\n✅ ¡Éxito! Webhook configurado en: {url}")
        else:
            print(f"\n❌ Error: {resultado.get('description')}")
    except Exception as e:
        print(f"\n❌ No se pudo conectar: {e}")

if __name__ == "__main__":
    configurar_webhook()