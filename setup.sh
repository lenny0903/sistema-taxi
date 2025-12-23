#!/bin/bash
#Para ejecutarlo
# 1) chmod +x setup.sh
# 2) ./setup.sh
echo "🔧 Iniciando setup del demo de taxis..."

# 1. Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
  echo "📦 Creando entorno virtual..."
  python3 -m venv venv
fi

# 2. Activar entorno virtual
echo "🚀 Activando entorno virtual..."
source venv/bin/activate

# 3. Instalar dependencias
echo "📚 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Inicializar base de datos y usuarios demo
echo "🗄️ Inicializando base de datos y usuarios..."
python3 - <<'EOF'
from app import create_app, db
from models.usuarios import Usuario
from models.roles import Rol

app = create_app()
with app.app_context():
    # Roles
    if not Rol.query.filter_by(id_rol=1).first():
        db.session.add(Rol(id_rol=1, nombre_rol="Administrador", descripcion="Rol administrador"))
        print("✅ Rol Administrador creado")
    if not Rol.query.filter_by(id_rol=2).first():
        db.session.add(Rol(id_rol=2, nombre_rol="Operador", descripcion="Rol operador"))
        print("✅ Rol Operador creado")

    # Usuarios
    if not Usuario.query.filter_by(username="admin1").first():
        admin = Usuario(username="admin1", nombre_completo="Administrador del sistema", rol_id=1, activo=True)
        admin.set_password("1234")
        db.session.add(admin)
        print("✅ Usuario admin1 creado con clave 1234")

    if not Usuario.query.filter_by(username="operador1").first():
        operador = Usuario(username="operador1", nombre_completo="Operador de despacho", rol_id=2, activo=True)
        operador.set_password("abcd")
        db.session.add(operador)
        print("✅ Usuario operador1 creado con clave abcd")

    db.session.commit()
    print("🚀 Inicialización automática completada")
EOF

echo "✅ Setup finalizado. Ahora puedes arrancar la app con:"
echo "python3 app.py"
