from datetime import datetime, timezone
from extensions import db

class BloqueoAfinidad(db.Model):
    __tablename__ = 'bloqueos_afinidad'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'))
    
    # Si tipo es 'CLIENTE_GENERAL', la alerta sale al poner el teléfono.
    # Si tipo es 'CONDUCTOR_EXCLUSION', se bloquea el match específico.
    tipo_bloqueo = db.Column(db.String(30), nullable=False) 
    
    activo = db.Column(db.Boolean, default=True) # El gerente lo apaga manualmente
    nota_gerencial = db.Column(db.String(255)) # Por qué se bloqueó
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)