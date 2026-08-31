from extensions import db
from datetime import datetime

class ColaDespacho(db.Model):
    __tablename__ = 'cola_despachos'

    id_cola = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    origen = db.Column(db.String(255), nullable=True)
    destino = db.Column(db.String(255), nullable=True)
    tarifa = db.Column(db.Numeric(10, 2), nullable=True, default=0) # 👈 Agregamos el campo tarifa
    estado = db.Column(db.String(20), nullable=False, default="En espera")
    fecha_creacion = db.Column(db.DateTime, default=datetime.now, nullable=False)

    cliente = db.relationship("Cliente", backref=db.backref("cola_despachos", lazy=True))

    def __repr__(self):
        return f"<ColaDespacho id_cola={self.id_cola}, id_cliente={self.id_cliente}, estado={self.estado}>"

    def to_dict(self):
        return {
            "id_cola": self.id_cola,
            "id_cliente": self.id_cliente,
            "origen": self.origen,
            "destino": self.destino,
            "tarifa": float(self.tarifa) if self.tarifa is not None else 0, # 👈 Se incluye en el diccionario
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "cliente": self.cliente.to_dict() if self.cliente else None
        }