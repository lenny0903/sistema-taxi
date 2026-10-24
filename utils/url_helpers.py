import requests


def acortar_url_cuttly(url_larga):
  # Reemplaza con tu API Key gratuita de Cuttly o guárdala en tu archivo .env
  api_key = "b56c22aeeafd65b7f5d7405d4abcf46f4c4f0"

  api_url = f"https://cutt.ly/api/api.php?key={api_key}&short={url_larga}"

  try:
    response = requests.get(api_url)
    data = response.json()

    # El código de estado 7 en Cuttly significa que se acortó exitosamente
    if data.get("url", {}).get("status") == 7:
      return data["url"]["shortLink"]
  except Exception as e:
    print(f"Error al conectar con la API de Cuttly: {e}")

  # Fallback: si algo falla, devuelve la URL larga original para que el sistema no se caiga
  return url_larga