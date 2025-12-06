#!/bin/bash
# Script de migración rápida para sistema Flask con SQLite
# Instrucciones para ejecutar: bash setup_flask_sqlite.sh
#  1) chmod +x setup_flask_sqlite.sh
#  2) ./setup_flask_sqlite.sh
# 1. Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# 2. Activar entorno virtual
echo "🔑 Activando entorno virtual..."
source venv/bin/activate

# 3. Instalar dependencias
if [ -f requirements.txt ]; then
    echo "📚 Instalando dependencias desde requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️ No se encontró requirements.txt. Instala dependencias manualmente."
fi

# 4. Verificar SQLite
echo "🗄️ Verificando SQLite..."
python3 - <<EOF
import sqlite3
print("✅ SQLite disponible:", sqlite3.sqlite_version)
EOF

# 5. Lanzar servidor Flask
echo "🚀 Iniciando servidor Flask..."
export FLASK_APP=app.py   # Ajusta si tu archivo principal tiene otro nombre
flask run --host=0.0.0.0 --port=5000
