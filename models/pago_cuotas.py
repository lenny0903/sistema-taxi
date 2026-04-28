from datetime import datetime, timezone
from extensions import db

class PagoCuota(db.Model):
    __tablename__ = 'pagos_cuotas'
    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), nullable=False)
    
    # Formato '2026-15' (Año-Semana) para búsquedas rápidas
    semana_anio = db.Column(db.String(10), nullable=False) 
    
    monto_pagado = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Clave para el Gerente: ¿Cómo pagó? (Efectivo, Zelle, Transferencia)
    metodo_pago = db.Column(db.String(20), default='Efectivo')
    referencia = db.Column(db.String(50)) # Nro de transferencia o recibo manual
    
    # Quién recibió el dinero
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))