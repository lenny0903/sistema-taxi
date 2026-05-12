from datetime import datetime, timezone
from extensions import db

class PagoCuota(db.Model):
    __tablename__ = 'pagos_cuotas'
    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), nullable=False)
    semana_anio = db.Column(db.String(10), nullable=False) 
    monto_pagado = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    metodo_pago = db.Column(db.String(20), default='Efectivo')
    referencia = db.Column(db.String(50))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))

    # 🆕 CAMPOS PARA LA TRAZABILIDAD DE EXONERACIONES
    es_exoneracion = db.Column(db.Boolean, default=False)
    tipo_incidencia = db.Column(db.String(50), nullable=True) # Ej: 'Enfermedad', 'Taller'
    observaciones = db.Column(db.Text, nullable=True)        # Para el detalle humano