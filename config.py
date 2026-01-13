import os
from dotenv import load_dotenv

# Cargar variables desde .env si existe
load_dotenv()

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta relativa a la base de datos SQLite
SQLITE_DB = os.getenv("SQLITE_DB", "taxis.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, SQLITE_DB)}"

# Configuración general de Flask
SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-demo")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Ejemplo de configuración futura para PostgreSQL/MySQL
# POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://user:pass@localhost/dbname")

