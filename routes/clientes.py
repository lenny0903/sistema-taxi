from flask import Blueprint, request, jsonify
from extensions import db
from models.clientes import Cliente

# Definición del Blueprint
clientes_bp = Blueprint('clientes', __name__, url_prefix="/clientes")

# Crear cliente
@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    data = request.get_json()
    telefono = data.get("telefono")

    if Cliente.query.filter_by(telefono=telefono).first():
        return jsonify({"error": "Teléfono ya registrado"}), 400

    nuevo = Cliente(
        telefono=telefono,
        nombre=data.get("nombre"),
        direccion=data.get("direccion")
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"msg": "Cliente creado", "id_cliente": nuevo.id_cliente}), 201

# Listar clientes
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    clientes = Cliente.query.all()
    resultado = [
        {"id_cliente": c.id_cliente, "telefono": c.telefono, "nombre": c.nombre, "direccion": c.direccion}
        for c in clientes
    ]
    return jsonify(resultado), 200

# Obtener cliente por ID
@clientes_bp.route('/<int:id>', methods=['GET'])
def obtener_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    return jsonify(cliente.to_dict())

# Buscar cliente por teléfono (query param)
@clientes_bp.route('/buscar', methods=['GET'])
def buscar_cliente():
    telefono = request.args.get('telefono')
    if telefono:
        cliente = Cliente.query.filter(Cliente.telefono == telefono).all()
        return jsonify([c.to_dict() for c in cliente])
    return jsonify([])

# Obtener o actualizar cliente por teléfono
@clientes_bp.route('/telefono/<string:telefono>', methods=['GET', 'PUT'])
def cliente_por_telefono(telefono):
    cliente = Cliente.query.filter_by(telefono=telefono).first()

    if request.method == "GET":
        if not cliente:
            return jsonify({"existe": False})
        return jsonify(cliente.to_dict())

    if request.method == "PUT":
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.get_json()
        actualizado = {}

        if "nombre" in data and data["nombre"].strip():
            cliente.nombre = data["nombre"].strip()
            actualizado["nombre"] = cliente.nombre

        if "direccion" in data and data["direccion"].strip():
            cliente.direccion = data["direccion"].strip()
            actualizado["direccion"] = cliente.direccion

        db.session.commit()
        return jsonify({
            "mensaje": "Cliente actualizado correctamente",
            "actualizado": actualizado
        }), 200


