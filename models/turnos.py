from datetime import datetime
from extensions import db

class Turno(db.Model):
    __tablename__ = "turnos"

    id_turno = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey("conductores.id_conductor"), nullable=False)
    auto_id = db.Column(db.Integer, db.ForeignKey("autos.id_auto"), nullable=False)
    estado = db.Column(db.String(20), default="activo")  # activo, finalizado
    inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fin = db.Column(db.DateTime)

    # Relaciones explícitas
    conductor = db.relationship("Conductor", backref="turnos", foreign_keys=[conductor_id])
    auto = db.relationship("Auto", backref="turnos", foreign_keys=[auto_id])

    def __repr__(self):
        return f"<Turno {self.id_turno} - Conductor {self.conductor_id} - Auto {self.auto_id} - Estado {self.estado}>"
    def to_dict(self):
        return {
            "id_turno": self.id_turno,
            "estado": self.estado,
            "inicio": self.inicio.isoformat(),
            "fin": self.fin.isoformat() if self.fin else None,
            "conductor": {
                "id_conductor": self.conductor.id_conductor if self.conductor else None,
                "nombre": self.conductor.nombre if self.conductor else None,
                "estado": self.conductor.estado if self.conductor else None
            },
            "auto": {
                "id_auto": self.auto.id_auto if self.auto else None,
                "placa": self.auto.nro_placa if self.auto else None,
                "marca": self.auto.marca if self.auto else None,
                "modelo": self.auto.modelo if self.auto else None
            }
        }