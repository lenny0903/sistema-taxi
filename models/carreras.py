from extensions import db
from datetime import datetime

# emplaza al papel transparente
class Destino(db.Model):
    __tablename__ = 'destinos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_ruta = db.Column(db.String(150), nullable=False, unique=True) # Ej: "Arjona 46/Centro"
    precio_cop = db.Column(db.Float, nullable=False) # Ej: 20000
    municipio = db.Column(db.String(100))
    es_combinacion = db.Column(db.String(2)) # "si" o "no"

# Esta es la que registra el movimiento diario
class Viaje(db.Model):
    __tablename__ = 'viajes'
    id = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    # REFERENCIA INTELIGENTE:
    # Aquí guardamos el nombre de la ruta para saber qué tarifa se aplicó
    ruta_base = db.Column(db.String(150), nullable=False) # Ej: "Arjona 46/Centro"
    
    # DETALLE ESPECÍFICO:
    # Aquí el operador escribe la dirección exacta que le da el cliente
    direccion_detallada = db.Column(db.String(255), nullable=False) # Ej: "Calle 2, Casa #45, frente al abasto"
    
    monto_cobrado_cop = db.Column(db.Float, nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id'))
    # ... otros campos como estatus o cliente