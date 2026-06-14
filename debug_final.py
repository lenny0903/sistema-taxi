import requests

TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
CHAT_ID = "1568216726" 
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

payload = {
    'chat_id': CHAT_ID,
    'text': "PRUEBA DESDE TERMINAL"
}

respuesta = requests.post(url, data=payload)
print(f"Estado: {respuesta.status_code}")
print(f"Respuesta: {respuesta.text}")