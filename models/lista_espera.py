# models/lista_espera.py
from extensions import db
from datetime import datetime

class ListaEspera(db.Model):
    __tablename__ = "lista_espera"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    origen = db.Column(db.String(255), nullable=False)
    destino = db.Column(db.String(255), nullable=False)
    hora = db.Column(db.DateTime, default=datetime.now)
    estado = db.Column(db.String(50), default="en espera")
    nro_telefono = db.Column(db.String(20)) 
    tarifa = db.Column(db.Float)
    # Relación con Cliente
    cliente = db.relationship("Cliente", backref="lista_espera")

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_nombre": self.cliente.nombre if self.cliente else None,
            "origen": self.origen,
            "destino": self.destino,
            "hora": self.hora.isoformat() if self.hora else None,
            "estado": self.estado,
            "nro_telefono": self.nro_telefono,
            "tarifa": self.tarifa
        }