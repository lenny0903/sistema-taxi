from datetime import datetime, timezone
from extensions import db

class CuotaSemanal(db.Model):
    __tablename__ = 'cuotas_semanales'
    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), nullable=False)
    semana_anio = db.Column(db.String(10), nullable=False) 
    monto_fijo = db.Column(db.Float, default=40000.0) # 👈 Actualizado a 40k
    pagado = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    referencia_pago = db.Column(db.String(50))