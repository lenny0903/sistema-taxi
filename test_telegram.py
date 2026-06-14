import requests

TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

response = requests.get(url)
print(f"Respuesta cruda del servidor: {response.text}")