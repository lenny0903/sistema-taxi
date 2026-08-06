import requests

def configurar_webhook():
    # Tu token (puedes dejarlo fijo o pedirlo también)
    
    
    print("--- Configuración automática de Webhook ---")
    url_tunel = input("Ingresa la URL de tu túnel (ej. https://xxx.trycloudflare.com): ").strip()
    
    # Asegurarnos de que termine en /telegram/webhook
    if not url_tunel.endswith('/telegram/webhook'):
        url_tunel = url_tunel.rstrip('/') + '/telegram/webhook'
    
    api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, data={'url': url_tunel})
        resultado = response.json()
        
        if resultado.get('ok'):
            print("\n✅ ¡Éxito! El Webhook ha sido configurado correctamente.")
            print(f"URL configurada: {url_tunel}")
        else:
            print("\n❌ Error al configurar el Webhook:")
            print(resultado.get('description'))
            
    except Exception as e:
        print(f"\n❌ No se pudo conectar con Telegram: {e}")

if __name__ == "__main__":
    configurar_webhook()