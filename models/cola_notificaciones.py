from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo

def hora_local():
    return datetime.now(ZoneInfo("America/Caracas"))

class ColaNotificaciones(db.Model):
    __tablename__ = 'cola_notificaciones'
    
    id_notificacion = db.Column(db.Integer, primary_key=True)
    turno_id = db.Column(db.Integer, nullable=False) # ID del despacho
    tipo_mensaje = db.Column(db.String(50), nullable=False) # 'FICHA_CLIENTE' o 'DETALLES_CONDUCTOR'
    destinatario_telefono = db.Column(db.String(20), nullable=False)
    contenido_json = db.Column(db.Text, nullable=False) # El payload completo
    estado = db.Column(db.String(20), default='PENDIENTE') # PENDIENTE, ENVIADO, ERROR, REINTENTANDO
    intentos = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=hora_local)
    fecha_envio = db.Column(db.DateTime, nullable=True)
    error_log = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id_notificacion,
            "turno_id": self.turno_id,
            "tipo": self.tipo_mensaje,
            "telefono": self.destinatario_telefono,
            "estado": self.estado
        }