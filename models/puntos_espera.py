from extensions import db

class PuntoEspera(db.Model):
    __tablename__ = "puntos_espera"

    id_punto = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)   # código interno
    nombre = db.Column(db.String(100), unique=True, nullable=False)  # nombre visible

    # Relación inversa con Turno
    turnos = db.relationship("Turno", back_populates="punto", lazy=True)

    def __repr__(self):
        return f"<PuntoEspera {self.codigo} - {self.nombre}>"

    def to_dict(self):
        return {
            "id_punto": self.id_punto,
            "codigo": self.codigo,
            "nombre": self.nombre
        }
