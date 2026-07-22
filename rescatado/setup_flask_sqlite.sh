#!/bin/bash
# Script de instalación rápida para sistema Flask con SQLite
# Uso:
#   chmod +x setup_flask_sqlite.sh
#   ./setup_flask_sqlite.sh

set -e  # Detener ejecución si ocurre un error

echo "🔍 Verificando dependencias del sistema..."

# Asegurar que python3-venv esté instalado
if ! dpkg -s python3-venv >/dev/null 2>&1; then
    echo "📦 Instalando python3-venv..."
    sudo apt update && sudo apt install -y python3-venv
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔑 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️ Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || echo "⚠️ Algunas dependencias fallaron, revisa requirements.txt"
else
    echo "⚠️ No se encontró requirements.txt, instalando paquetes básicos..."
    pip install flask python-dotenv sqlalchemy
fi

# Verificar SQLite
echo "🗄️ Verificando SQLite..."
sqlite3 --version || { echo "❌ SQLite no está disponible"; exit 1; }

# Verificar Flask
if ! command -v flask >/dev/null 2>&1; then
    echo "❌ Flask no está instalado en el entorno virtual"
    exit 1
fi

# Iniciar servidor Flask
echo "🚀 Iniciando servidor Flask..."
export FLASK_APP=app.py   # Ajusta si tu archivo principal se llama distinto
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000

