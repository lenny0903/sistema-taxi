from extensions import db

class Rol(db.Model):
    __tablename__ = 'roles'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return (
            f"<Rol id={self.id_rol}, "
            f"nombre={self.nombre_rol}, "
            f"descripcion={self.descripcion}>"
        )
    def to_dict(self):
        return {
            "id_rol": self.id_rol,
            "nombre_rol": self.nombre_rol,
            "descripcion": self.descripcion
        }
