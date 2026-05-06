from extensions import db
#from utils import db


class MatrizTarifa(db.Model):
    __tablename__ = 'matriz_tarifas' # Debe coincidir exactamente con el nombre en SQLite

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    destino = db.Column(db.Text, nullable=False)
    precio_cop = db.Column(db.Float) # REAL en SQL se mapea como Float en SQLAlchemy
    municipio = db.Column(db.Text)
    es_combinacion = db.Column(db.Text) # "si" o "no"

    def __repr__(self):
        return f'<Tarifa {self.destino}: {self.precio_cop} COP>'