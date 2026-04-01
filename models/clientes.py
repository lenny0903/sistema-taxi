import datetime
from extensions import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    punto_referencia = db.Column(db.Text, nullable=True)

    # --- NUEVOS CAMPOS PARA TRAZABILIDAD ---
    estado = db.Column(db.Integer, default=1)  # 1=Activo, 0=Inactivo
    #usuario_id_auditoria = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    #fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Cliente id={self.id_cliente}, "
            f"nombre={self.nombre}, "
            f"telefono={self.telefono}, "
            f"estado={self.estado}>"
        )
    def to_dict(self):
        return {
            "id_cliente": self.id_cliente,
            "telefono": self.telefono,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "estado": self.estado
            #"punto_referencia": self.punto_referencia
        }