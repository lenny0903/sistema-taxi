from datetime import datetime, timezone
from extensions import db

class BloqueoAfinidad(db.Model):
    __tablename__ = 'bloqueos_afinidad'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), nullable=True)
    
    # Si tipo es 'CLIENTE_GENERAL', la alerta sale al poner el teléfono.
    # Si tipo es 'CONDUCTOR_EXCLUSION', se bloquea el match específico.
    tipo_bloqueo = db.Column(db.String(30), nullable=False) 
    
    activo = db.Column(db.Boolean, default=True)
    nota_gerencial = db.Column(db.String(255), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Incidencia(db.Model):
    __tablename__ = 'incidencias'
    id = db.Column(db.Integer, primary_key=True)
    despacho_id = db.Column(db.Integer, db.ForeignKey('despachos.id_despacho'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), nullable=True)
    
    categoria = db.Column(db.String(20), nullable=False) 
    descripcion = db.Column(db.Text, nullable=False)
    
    fecha_reporte = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    operador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)