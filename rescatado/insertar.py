from extensions import db
from models.usuarios import Usuario
from models.roles import Rol
from werkzeug.security import generate_password_hash
from app import create_app

app = create_app()

with app.app_context():
    # 1. Borrar usuarios existentes
    Usuario.query.delete()
    db.session.commit()
    print("✅ Usuarios eliminados")

    # 2. Crear roles básicos
    Rol.query.delete()
    db.session.commit()

    admin_role = Rol(id_rol=1, nombre_rol="Administrador")
    operador_role = Rol(id_rol=2, nombre_rol="Operador")
    db.session.add(admin_role)
    db.session.add(operador_role)
    db.session.commit()
    print("✅ Roles creados")

    # 3. Crear usuarios iniciales
    admin = Usuario(
        username="admin",
        password_hash=generate_password_hash("1234"),
        nombre_completo="Administrador del sistema",
        rol_id=1,
        activo=True
    )
    operador = Usuario(
        username="operador",
        password_hash=generate_password_hash("1234"),
        nombre_completo="Operador de despacho",
        rol_id=2,
        activo=True
    )
    db.session.add(admin)
    db.session.add(operador)
    db.session.commit()
    print("✅ Usuarios iniciales creados")
    print("✅ Inserción completada")