from extensions import db

class ListaEsperaMultiple(db.Model):
    __tablename__ = "lista_espera_multiple"

    id_lista_multiple = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    iteraciones = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="en espera")

    # Relación opcional para acceder al cliente directamente
    cliente = db.relationship("Cliente", backref="esperas_multiples")
