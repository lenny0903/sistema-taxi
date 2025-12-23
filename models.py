from app import db

class Rol(db.Model):
    __tablename__ = 'roles'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    clave_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo = db.Column(db.Boolean, default=True)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_clientes = db.Column(db.Integer, primary_key=True)
    nro_telefono = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.Text)

class Conductor(db.Model):
    __tablename__ = 'conductores'
    id_conductores = db.Column(db.Integer, primary_key=True)
    cod_conductor = db.Column(db.String(20), unique=True, nullable=False)
    nro_telefono = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)

class Auto(db.Model):
    __tablename__ = 'autos'
    id_autos = db.Column(db.Integer, primary_key=True)
    nro_placa = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))

class Despacho(db.Model):
    __tablename__ = 'despacho'
    id_despacho = db.Column(db.Integer, primary_key=True)
    origen = db.Column(db.Text, nullable=False)
    destino = db.Column(db.Text, nullable=False)
    tarifa = db.Column(db.Numeric(10,2))
    estado_despacho = db.Column(db.String(20), default='en curso')
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id_clientes'), nullable=False)
    conductor_id = db.Column(db.Integer, db.ForeignKey('conductores.id_conductores'))
    auto_id = db.Column(db.Integer, db.ForeignKey('autos.id_autos'))
