from extensions import db
from datetime import datetime

class Despacho(db.Model):
    __tablename__ = "despachos"

    id_despacho = db.Column(db.Integer, primary_key=True)

    # Datos básicos del despacho
    origen_despacho = db.Column(db.String(100), nullable=False)
    destino_despacho = db.Column(db.String(100), nullable=False)
    fecha_hora_embarque = db.Column(db.DateTime, nullable=True)

    # Relaciones con otras entidades
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey("conductores.id_conductor"), nullable=False)
    auto_id = db.Column(db.Integer, db.ForeignKey("autos.id_auto"), nullable=False)
    
    # Campos de negocio
    tarifa = db.Column(db.Float, nullable=False)
    estado_despacho = db.Column(db.String(50), default="pendiente", nullable=False)

    # Trazabilidad temporal
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False, default=datetime.now)
    fecha_hora_fin = db.Column(db.DateTime, nullable=True)

    # Relaciones ORM
    cliente = db.relationship("Cliente", backref="despachos")
    conductor = db.relationship("Conductor", backref="despachos")
    auto = db.relationship("Auto", backref="despachos")

    def __repr__(self):
        return f"<Despacho {self.id_despacho} - {self.origen_despacho} → {self.destino_despacho}>"
    def to_dict(self):
        return {
            "id_despacho": self.id_despacho,
            "origen_despacho": self.origen_despacho,
            "destino_despacho": self.destino_despacho,
            "fecha_hora_embarque": self.fecha_hora_embarque.isoformat() if self.fecha_hora_embarque else None,
            "cliente_id": self.cliente_id,
            "conductor_id": self.conductor_id,
            "auto_id": self.auto_id,
            "tarifa": self.tarifa,
            "estado_despacho": self.estado_despacho,
            "fecha_hora_inicio": self.fecha_hora_inicio.isoformat(),
            "fecha_hora_fin": self.fecha_hora_fin.isoformat() if self.fecha_hora_fin else None,
            "telefono": self.cliente.telefono if self.cliente else None
        }