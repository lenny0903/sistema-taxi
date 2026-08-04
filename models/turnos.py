from models.puntos_espera import PuntoEspera
from extensions import db
from datetime import datetime, timedelta
import pytz

def hora_venezuela():
    return datetime.now()
class Turno(db.Model):
    __tablename__ = "turnos"

    id_turno = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey("conductores.id_conductor"), nullable=False)
    auto_id = db.Column(db.Integer, db.ForeignKey("autos.id_auto"), nullable=False)
    punto_id = db.Column(db.Integer, db.ForeignKey("puntos_espera.id_punto"), nullable=False)  # nuevo campo
    estado = db.Column(db.String(20), default="activo")  # activo, finalizado
    inicio = db.Column(db.DateTime, default=hora_venezuela)
    fin = db.Column(db.DateTime)

    # Relaciones explícitas
    conductor = db.relationship("Conductor", backref="turnos", foreign_keys=[conductor_id])
    auto = db.relationship("Auto", backref="turnos", foreign_keys=[auto_id])
    punto = db.relationship("PuntoEspera", back_populates="turnos", foreign_keys=[punto_id])

    def __repr__(self):
        return f"<Turno {self.id_turno} - Conductor {self.conductor_id} - Auto {self.auto_id} - Punto {self.punto_id} - Estado {self.estado}>"

   

    def to_dict(self):
        return {
            "id_turno": self.id_turno,
            "estado": self.estado,
            # Como la fecha ya se guardó con la hora local real, solo le pegamos el sufijo -04:00
            "inicio": self.inicio.isoformat() + "-04:00" if self.inicio else None,
            "fin": self.fin.isoformat() + "-04:00" if self.fin else None,
            "conductor": {
                "id_conductor": self.conductor.id_conductor if self.conductor else None,
                "nombre": self.conductor.nombre if self.conductor else None,
                "estado": self.conductor.estado if self.conductor else None,
                "ultima_actualizacion": self.conductor.ultima_actualizacion.isoformat() + "-04:00" if (self.conductor and self.conductor.ultima_actualizacion) else None
            },
            "auto": {
                "id_auto": self.auto.id_auto if self.auto else None,
                "placa": self.auto.nro_placa if self.auto else None,
                "marca": self.auto.marca if self.auto else None,
                "modelo": self.auto.modelo if self.auto else None
            },
            "punto": {
                "id_punto": self.punto.id_punto if self.punto else None,
                "codigo": self.punto.codigo if self.punto else None,
                "nombre": self.punto.nombre if self.punto else None
            }
        }