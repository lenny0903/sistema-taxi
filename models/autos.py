from extensions import db

class Auto(db.Model):
    __tablename__ = 'autos'
    id_auto = db.Column(db.Integer, primary_key=True)
    nro_placa = db.Column(db.String(20), unique=True, nullable=False)
    tipo_auto = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="Disponible")

    def __repr__(self):
        return (
            f"<Auto id={self.id_auto}, "
            f"nro_placa={self.nro_placa}, "
            f"marca={self.marca}, "
            f"modelo={self.modelo}, "
            f"estado={self.estado}, "
            f"tipo={self.tipo_auto}>"
        )
    def to_dict(self):
        return {
            "id_auto": self.id_auto,
            "nro_placa": self.nro_placa,
            "tipo_auto": self.tipo_auto,
            "marca": self.marca,
            "modelo": self.modelo,
            "estado": self.estado
        }