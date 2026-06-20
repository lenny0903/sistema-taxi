import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SQLITE_DB = os.getenv("SQLITE_DB", "taxis.db")
db_path = os.path.join(BASE_DIR, SQLITE_DB)

SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

# --- AÑADE ESTO PARA EVITAR "DATABASE IS LOCKED" ---
SQLALCHEMY_ENGINE_OPTIONS = {
    "connect_args": {
        "timeout": 20  # Espera hasta 20 segundos si otro proceso está usando el archivo
    }
}
# ---------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-demo")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# AÑADE ESTA LÍNEA PARA TENER CONTROL TOTAL
FLASK_ENV = os.getenv("FLASK_ENV", "production") 

print(f"[*] Base de datos activa en: {db_path}")
print(f"[*] Modo Debug: {DEBUG} | Entorno: {FLASK_ENV}")