from extensions import db

class Reserva(db.Model):
    __tablename__ = "reservas"

    id_reserva = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    origen = db.Column(db.String(120), nullable=False)
    destino = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    estado = db.Column(db.String(20), default="activo")
    notificada = db.Column(db.Boolean, default=False)
    cliente = db.relationship("Cliente", backref="reservas")

    def to_dict(self):
        return {
            "id_reserva": self.id_reserva,
            "cliente_id": self.cliente_id,
            "origen": self.origen,
            "destino": self.destino,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora": self.hora.strftime("%H:%M:%S") if self.hora else None,
            "estado": self.estado,
            "notificada": self.notificada,
            "cliente": {
                "id_cliente": self.cliente.id_cliente if self.cliente else None,
                "nombre": self.cliente.nombre if self.cliente else None,
                "telefono": self.cliente.telefono if self.cliente else None,
                "direccion": self.cliente.direccion if self.cliente else None,
                #"punto_referencia": self.cliente.punto_referencia if self.cliente else None,
            }
        }
