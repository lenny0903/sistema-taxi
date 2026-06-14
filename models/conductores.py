from extensions import db
from datetime import datetime

class Conductor(db.Model):
    __tablename__ = 'conductores'
    id_conductor = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    nro_cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    nro_telefono = db.Column(db.String(20), unique=True, nullable=False)
    estado = db.Column(db.String(50), default="disponible", nullable=False)
    telegram_id = db.Column(db.String(50), nullable=True, unique=True)
    
    # Nuevos campos para geolocalización
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Conductor {self.nombre} ({self.codigo})>"

    def to_dict(self):
        return {
            "id_conductor": self.id_conductor,
            "codigo": self.codigo,
            "nro_cedula": self.nro_cedula,
            "nombre": self.nombre,
            "nro_telefono": self.nro_telefono,
            "estado": self.estado,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "ultima_actualizacion": self.ultima_actualizacion.isoformat() if self.ultima_actualizacion else None
        }