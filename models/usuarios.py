from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    # 👇 Mapeo: la columna en la BD se llama "usuario", pero en tu código usas "username"
    username = db.Column("usuario", db.String(50), unique=True, nullable=False)
    # 👇 Mapeo: la columna en la BD se llama "clave_hash"
    password_hash = db.Column("clave_hash", db.String(128), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    rol = db.relationship('Rol', backref=db.backref('usuarios', lazy=True))

    def __repr__(self):
        return (
            f"<Usuario id={self.id_usuario}, "
            f"username={self.username}, "
            f"rol_id={self.rol_id}, "
            f"activo={self.activo}>"
        )
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)    