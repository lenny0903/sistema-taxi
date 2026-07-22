# init_demo.py
from app import create_app, db
from models.usuarios import Usuario
from models.roles import Rol
from flask import url_for
from werkzeug.security import check_password_hash

def init_demo():
    app = create_app()
    with app.app_context():
        print("🔧 Inicializando demo...")

        # Crear roles si no existen
        if not Rol.query.filter_by(id_rol=1).first():
            admin_role = Rol(id_rol=1, nombre_rol="Administrador", descripcion="Rol administrador")
            db.session.add(admin_role)
            print("✅ Rol Administrador creado")

        if not Rol.query.filter_by(id_rol=2).first():
            operador_role = Rol(id_rol=2, nombre_rol="Operador", descripcion="Rol operador")
            db.session.add(operador_role)
            print("✅ Rol Operador creado")

        # Crear usuario admin1
        if not Usuario.query.filter_by(username="admin1").first():
            admin = Usuario(username="admin1", nombre_completo="Administrador del sistema", rol_id=1, activo=True)
            admin.set_password("1234")
            db.session.add(admin)
            print("✅ Usuario admin1 creado con clave 1234")

        # Crear usuario operador1
        if not Usuario.query.filter_by(username="operador1").first():
            operador = Usuario(username="operador1", nombre_completo="Operador de despacho", rol_id=2, activo=True)
            operador.set_password("abcd")
            db.session.add(operador)
            print("✅ Usuario operador1 creado con clave abcd")

        db.session.commit()

        # Verificar rutas registradas
        print("📌 Rutas registradas:")
        for rule in app.url_map.iter_rules():
            print(rule)

        print("🚀 Demo inicializado correctamente. Ahora prueba el login con:")
        print("curl -X POST http://127.0.0.1:5000/auth/login "
              "-H 'Content-Type: application/json' "
              "-d '{\"username\":\"admin1\",\"password\":\"1234\"}'")

if __name__ == "__main__":
    init_demo()
