from extensions import db
from models.usuarios import Usuario
from models.roles import Rol
from app import create_app

app = create_app()

with app.app_context():
    # Crear roles si no existen
    if not Rol.query.filter_by(id_rol=1).first():
        admin_role = Rol(id_rol=1, nombre_rol="Administrador", descripcion="Rol administrador")
        db.session.add(admin_role)

    if not Rol.query.filter_by(id_rol=2).first():
        operador_role = Rol(id_rol=2, nombre_rol="Operador", descripcion="Rol operador")
        db.session.add(operador_role)

    # Crear usuario admin1
    if not Usuario.query.filter_by(username="admin1").first():
        admin = Usuario(username="admin1", nombre_completo="Administrador del sistema", rol_id=1, activo=True)
        admin.set_password("1234")
        db.session.add(admin)

    # Crear usuario operador1
    if not Usuario.query.filter_by(username="operador1").first():
        operador = Usuario(username="operador1", nombre_completo="Operador de despacho", rol_id=2, activo=True)
        operador.set_password("abcd")
        db.session.add(operador)

    db.session.commit()
    print("✅ Usuarios inicializados: admin1 (1234) y operador1 (abcd)")
