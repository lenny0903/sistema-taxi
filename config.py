import os
from dotenv import load_dotenv
from sqlalchemy import event  # 1. IMPORTA ESTO AQUÍ
from sqlalchemy import create_engine # 2. Asegúrate de importar esto

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SQLITE_DB = os.getenv("SQLITE_DB", "taxis.db")
db_path = os.path.join(BASE_DIR, SQLITE_DB)

SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

# --- MANTÉN TU CONFIGURACIÓN DE TIMEOUT ---
SQLALCHEMY_ENGINE_OPTIONS = {
    "connect_args": {
        "timeout": 20
    }
}

# --- AÑADE ESTO PARA ACTIVAR MODO WAL (BLOQUEO CERO) ---
@event.listens_for(create_engine('sqlite:///dummy.db'), "connect") # Nota: es un listener genérico
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
# --------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-demo")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

FLASK_ENV = os.getenv("FLASK_ENV", "production") 

print(f"[*] Base de datos activa en: {db_path}")
print(f"[*] Modo Debug: {DEBUG} | Entorno: {FLASK_ENV}")