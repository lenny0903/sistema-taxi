import re
from flask import Blueprint, request, jsonify
from extensions import db
from models.clientes import Cliente

# Definición del Blueprint
clientes_bp = Blueprint('clientes', __name__, url_prefix="/clientes")

def validar_nombre(nombre: str) -> bool:
    if not nombre:
        return False
    nombre = nombre.strip()
    if len(nombre) < 2 or len(nombre) > 50:
        return False
    return True


# 🔹 Crear cliente
@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    data = request.get_json()
    telefono = data.get("nro_telefono") or data.get("telefono")
    if not telefono:
        return jsonify({"error": "Teléfono es obligatorio"}), 400

    if Cliente.query.filter_by(telefono=telefono).first():
        return jsonify({"error": "Teléfono ya registrado"}), 400

    nombre = (data.get('nombre') or "").strip()
    # 🔹 Validación mínima: no vacío y al menos 2 caracteres
    if not validar_nombre(nombre):
        return jsonify({"error": "Nombre inválido"}), 400

    cliente = Cliente(
        nombre=nombre,
        telefono=telefono,
        direccion=data.get('direccion'),
        punto_referencia=(data.get('punto_referencia') or "").strip() or None
    )
    db.session.add(cliente)
    db.session.commit()
    return jsonify({
        "message": "Cliente creado",
        "id_cliente": cliente.id_cliente,
        "punto_referencia": cliente.punto_referencia
    }), 201


# 🔹 Modificar cliente por teléfono
@clientes_bp.route('/telefono/<telefono>', methods=['PUT'])
def actualizar_cliente_por_telefono(telefono):
    data = request.get_json()
    cliente = Cliente.query.filter_by(telefono=telefono).first()
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Validar nombre si se envía
    if 'nombre' in data and not validar_nombre(data['nombre']):
        return jsonify({"error": "Nombre inválido"}), 400

    # Actualizar campos con fallback
    cliente.nombre = data.get('nombre', cliente.nombre)
    cliente.direccion = data.get('direccion', cliente.direccion)
    cliente.punto_referencia = data.get('punto_referencia', cliente.punto_referencia)

    db.session.commit()
    return jsonify({
        "message": "Cliente actualizado",
        "id_cliente": cliente.id_cliente,
        "punto_referencia": cliente.punto_referencia
    }), 200

# Listar clientes
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    clientes = Cliente.query.all()
    resultado = [
        {
            "id_cliente": c.id_cliente,
            "telefono": c.telefono,
            "nombre": c.nombre,
            "direccion": c.direccion,
            "punto_referencia": c.punto_referencia  # 🔹 faltaba este campo
        }
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


