import os
from dotenv import load_dotenv

load_dotenv()

# 1. Aseguramos que BASE_DIR sea la raíz (subimos un nivel si config.py está en subcarpeta)
# Si config.py ya está en la raíz, usa solo un os.path.dirname
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Si este archivo está en una carpeta como 'utils', descomenta la siguiente línea:
# BASE_DIR = os.path.dirname(BASE_DIR) 

# 3. Limpieza de la URI (Compatibilidad total Windows/Linux)
SQLITE_DB = os.getenv("SQLITE_DB", "taxis.db")
db_path = os.path.join(BASE_DIR, SQLITE_DB)

# El triple slash 'sqlite:///' es crucial. 
# En Windows, os.path.join pondrá 'C:\...', y en Linux '/home/...'
SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

# Imprime esto en la consola al arrancar para que veas qué archivo está abriendo
print(f"[*] Base de datos activa en: {db_path}")

SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-demo")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")