from extensions import db

class Conductor(db.Model):
    __tablename__ = 'conductores'
    id_conductor = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    nro_cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    nro_telefono = db.Column(db.String(20), unique=True, nullable=False)
    estado = db.Column(db.String(50), default="disponible", nullable=False)

    def __repr__(self):
        return (
            f"<Conductor id={self.id_conductor}, "
            f"codigo={self.codigo}, "
            f"nro_cedula={self.nro_cedula}, "
            f"nombre={self.nombre}, "
            f"nro_telefono={self.nro_telefono}, "
            f"estado={self.estado}>"
        )
    def to_dict(self):
        return {
            "id_conductor": self.id_conductor,
            "codigo": self.codigo,
            "nro_cedula": self.nro_cedula,
            "nombre": self.nombre,
            "nro_telefono": self.nro_telefono,
            "estado": self.estado
        }