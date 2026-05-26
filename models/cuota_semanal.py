from datetime import datetime, timezone
from extensions import db

class CuotaSemanal(db.Model):
    __tablename__ = 'cuotas_semanales'
    id = db.Column(db.Integer, primary_key=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductor'), index=True, nullable=False)
    semana_anio = db.Column(db.String(10), index=True, nullable=False)
    monto_fijo = db.Column(db.Float, default=40000.0)
    pagado = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    referencia_pago = db.Column(db.String(50))

    # 🆕 NUEVOS CAMPOS PARA EL REGISTRO DE INCIDENCIAS/EXONERACIONES
    es_exonerado = db.Column(db.Boolean, default=False) 
    tipo_novedad = db.Column(db.String(50), nullable=True) 
    observaciones = db.Column(db.Text, nullable=True)     

    # =========================================================================
    # 🚨 EL ESCUDO DE ACERO: Restricción Única Compuesta NAtiva
    # =========================================================================
    # Esto le prohíbe terminantemente a SQLite duplicar la misma semana para el mismo chofer.
    # Si la ráfaga intenta meter dos registros iguales en el mismo milisegundo,
    # la base de datos aborta con un 'IntegrityError' y protege la contabilidad.
    __table_args__ = (
        db.UniqueConstraint('conductor_id', 'semana_anio', name='_conductor_semana_uc'),
    )