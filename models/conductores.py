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
    
    # Campos para geolocalización
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Nuevos campos para tiempo de expiración GPS
    opcion_gps = db.Column(db.String(20), nullable=True)        # Ej: '15 min', '1 hora', '8 horas'
    expiracion_gps = db.Column(db.DateTime, nullable=True)     # Hora exacta en la que vence
    alerta_enviada = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Conductor {self.nombre} ({self.codigo})>"

    def to_dict(self):
        # Calcular tiempo restante al convertir a diccionario
        ahora = datetime.now()
        tiempo_restante = "Desconocido"
        
        if self.expiracion_gps and self.expiracion_gps > ahora:
            diferencia = self.expiracion_gps - ahora
            horas, resto = divmod(diferencia.seconds, 3600)
            minutos, _ = divmod(resto, 60)
            tiempo_restante = f"{horas}h {minutos}m restantes" if horas > 0 else f"{minutos}m restantes"
        elif self.expiracion_gps and self.expiracion_gps <= ahora:
            tiempo_restante = "Expirado"

        return {
            "id_conductor": self.id_conductor,
            "codigo": self.codigo,
            "nro_cedula": self.nro_cedula,
            "nombre": self.nombre,
            "nro_telefono": self.nro_telefono,
            "estado": self.estado,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "ultima_actualizacion": self.ultima_actualizacion.isoformat() if self.ultima_actualizacion else None,
            "opcion_gps": self.opcion_gps or "En vivo",
            "tiempo_restante": tiempo_restante,
            "alerta_enviada": self.alerta_enviada
        }