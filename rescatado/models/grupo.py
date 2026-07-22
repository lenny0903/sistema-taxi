from extensions import db

class Grupo(db.Model):
    __tablename__ = "grupos"

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.String(50), unique=True, nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    origen = db.Column(db.String(200), nullable=False)
    destino = db.Column(db.String(200), nullable=False)
    tarifa = db.Column(db.Float, nullable=False)
    num_autos = db.Column(db.Integer, nullable=False)

    # Relación inversa con Despacho
    despachos = db.relationship("Despacho", back_populates="grupo")

    def __repr__(self):
        return f"<Grupo {self.grupo_id} - Cliente {self.cliente}>"

    def to_dict(self):
        return {
            "id": self.id,
            "grupo_id": self.grupo_id,
            "cliente": self.cliente,
            "telefono": self.telefono,
            "origen": self.origen,
            "destino": self.destino,
            "tarifa": self.tarifa,
            "num_autos": self.num_autos,
            "despachos": [d.id_despacho for d in self.despachos]  # lista de IDs asociados
        }
