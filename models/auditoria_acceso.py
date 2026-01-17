from extensions import db

class AuditoriaAcceso(db.Model):
    __tablename__ = 'auditoria_acceso'
    id = db.Column(db.Integer, primary_key=True)
    usuario_nombre = db.Column(db.String(50), nullable=False)
    evento = db.Column(db.String(20), nullable=False) # 'LOGIN' o 'LOGOUT'
    fecha_hora = db.Column(db.DateTime, default=db.func.current_timestamp())
    ip_address = db.Column(db.String(45)) # Para saber si entraron desde el local o por VPN
    user_agent = db.Column(db.String(255)) # Navegador/Dispositivo