from zoneinfo import ZoneInfo
from models.grupo import Grupo
from extensions import db
from datetime import datetime
import pytz


class Despacho(db.Model):
    __tablename__ = "despachos"

    id_despacho = db.Column(db.Integer, primary_key=True, autoincrement=True)


    # Datos básicos del despacho
    origen_despacho = db.Column(db.String(200), nullable=False)
    destino_despacho = db.Column(db.String(200), nullable=True)
    fecha_hora_embarque = db.Column(db.DateTime, nullable=True)
    telegram_id_cliente = db.Column(db.String(50), nullable=True)
    # Relaciones con otras entidades
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey("conductores.id_conductor"), nullable=False)
    auto_id = db.Column(db.Integer, db.ForeignKey("autos.id_auto"), nullable=False)
    
    # Campos de negocio
    tarifa = db.Column(db.Float, nullable=False)
    estado_despacho = db.Column(db.String(50), default="pendiente", nullable=False)
    calificacion = db.Column(db.Integer, nullable=True)          # Guardará la cantidad de estrellas (ej. 1, 3, 5)
    fecha_calificacion = db.Column(db.DateTime, nullable=True)
    comentario_calificacion = db.Column(db.Text, nullable=True)
    # Trazabilidad temporal
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False, default=datetime.now)
    fecha_hora_fin = db.Column(db.DateTime, nullable=True)

    # 🔹 Relación con Grupo (única definición de grupo_id)
    grupo_id = db.Column(db.String(50), db.ForeignKey("grupos.grupo_id"), index=True, nullable=True)
    grupo = db.relationship("Grupo", back_populates="despachos")

    # Relaciones ORM
    cliente = db.relationship("Cliente", backref="despachos")
    conductor = db.relationship("Conductor", backref="despachos")
    auto = db.relationship("Auto", backref="despachos")

    def __repr__(self):
        return f"<Despacho {self.id_despacho} - {self.origen_despacho} ({self.estado_despacho})>"
    
    TZ_CARACAS = pytz.timezone("America/Caracas")
    
    def to_dict(self):
        return {
            "id_despacho": self.id_despacho,
            "cliente_id": self.cliente_id,
            "conductor_id": self.conductor_id,
            "auto_id": self.auto_id,
            "origen_despacho": self.origen_despacho,
            "destino_despacho": self.destino_despacho,
            "fecha_hora_inicio": self.fecha_hora_inicio.astimezone(self.TZ_CARACAS).isoformat() if self.fecha_hora_inicio else None,
            "fecha_hora_fin": self.fecha_hora_fin.astimezone(self.TZ_CARACAS).isoformat() if self.fecha_hora_fin else None,
            "telegram_id_cliente": self.telegram_id_cliente,
            "calificacion": self.calificacion,
            "fecha_calificacion": self.fecha_calificacion.astimezone(self.TZ_CARACAS).isoformat() if self.fecha_calificacion else None,
            "tarifa": float(self.tarifa) if self.tarifa is not None else None,
            "estado_despacho": self.estado_despacho,
            "cliente": self.cliente.to_dict() if self.cliente else None,
            "conductor": self.conductor.to_dict() if self.conductor else None,
            "auto": self.auto.to_dict() if self.auto else None,
            "comentario_calificacion": self.comentario_calificacion
        }
