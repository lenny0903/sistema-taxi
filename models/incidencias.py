from datetime import datetime, timezone
from extensions import db

class Incidencia(db.Model):
    __tablename__ = 'incidencias'
    id = db.Column(db.Integer, primary_key=True)
    despacho_id = db.Column(db.Integer, db.ForeignKey('despachos.id_despacho'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'))
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), nullable=True)
    
    categoria = db.Column(db.String(20), nullable=False) 
    descripcion = db.Column(db.Text, nullable=False)
    
    # CAMBIA ESTA LÍNEA:
    fecha_reporte = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    operador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))