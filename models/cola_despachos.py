from extensions import db
from datetime import datetime

class ColaDespacho(db.Model):
    __tablename__ = 'cola_despachos'

    id_cola = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="En espera")
    nro_autos = db.Column(db.Integer, nullable=False, default=1)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con Cliente
    cliente = db.relationship("Cliente", backref=db.backref("cola_despachos", lazy=True))

    def __repr__(self):
        return (
            f"<ColaDespacho id_cola={self.id_cola}, "
            f"id_cliente={self.id_cliente}, "
            f"estado={self.estado}, "
            f"nro_autos={self.nro_autos}>"
        )

    def to_dict(self):
        return {
            "id_cola": self.id_cola,
            "id_cliente": self.id_cliente,
            "estado": self.estado,
            "nro_autos": self.nro_autos,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "cliente": self.cliente.to_dict() if self.cliente else None
        }
