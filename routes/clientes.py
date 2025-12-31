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
#Validación de teléfono
def validar_telefono(telefono: str) -> bool:
    if not telefono:
        return False
    patron = re.compile(r"^(0276[0-9]{7}|04[0-9]{9})$")
    return bool(patron.match(telefono))

# 🔹 Crear cliente
@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    data = request.get_json()
    telefono = data.get("nro_telefono") or data.get("telefono")
    if not telefono:
        return jsonify({"error": "Teléfono es obligatorio"}), 400

    # 🔹 Validación de formato
    if not validar_telefono(telefono):
        return jsonify({"error": "Teléfono inválido. Debe comenzar con 0276 (fijo) o 04 (móvil) y tener 11 dígitos"}), 400

    if Cliente.query.filter_by(telefono=telefono).first():
        return jsonify({"error": "Teléfono ya registrado"}), 400

    nombre = (data.get('nombre') or "").strip()
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

    if 'telefono' in data:
        nuevo_tel = data['telefono']
        if not validar_telefono(nuevo_tel):
            return jsonify({"error": "Teléfono inválido"}), 400
        cliente.telefono = nuevo_tel

    if 'nombre' in data and not validar_nombre(data['nombre']):
        return jsonify({"error": "Nombre inválido"}), 400

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
            "nro_telefono": c.telefono,
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
            return jsonify({"existe": False}), 200
        return jsonify({
            "existe": True,
            **cliente.to_dict()
        }), 200

    if request.method == "PUT":
        if not cliente:
            return jsonify({"error": "Cliente no encontrado", "existe": False}), 404

        data = request.get_json()
        actualizado = {}

        if "nombre" in data and data["nombre"].strip():
            cliente.nombre = data["nombre"].strip()
            actualizado["nombre"] = cliente.nombre

        if "direccion" in data and data["direccion"].strip():
            cliente.direccion = data["direccion"].strip()
            actualizado["direccion"] = cliente.direccion

        if "punto_referencia" in data and data["punto_referencia"].strip():
            cliente.punto_referencia = data["punto_referencia"].strip()
            actualizado["punto_referencia"] = cliente.punto_referencia

        db.session.commit()
        return jsonify({
            "mensaje": "Cliente actualizado correctamente",
            "existe": True,
            "id_cliente": cliente.id_cliente,
            **actualizado
        }), 200

@clientes_bp.route('/delete', methods=['POST'])
def eliminar_cliente():
    data = request.get_json()
    nombre = (data.get("nombre") or "").strip()

    if not validar_nombre(nombre):
        return jsonify({"error": "Nombre inválido"}), 400

    cliente = Cliente.query.filter_by(nombre=nombre).first()
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"message": f"Cliente {nombre} eliminado"}), 200

@clientes_bp.route('/updateTelefono', methods=['POST'])
def update_telefono():
    data = request.get_json()
    nombre = (data.get("nombre") or "").strip()
    nuevo_tel = (data.get("telefono") or "").strip()

    if not validar_nombre(nombre):
        return jsonify({"error": "Nombre inválido"}), 400
    if not validar_telefono(nuevo_tel):
        return jsonify({"error": "Teléfono inválido"}), 400

    cliente = Cliente.query.filter_by(nombre=nombre).first()
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    cliente.telefono = nuevo_tel
    db.session.commit()
    return jsonify({"message": "Teléfono actualizado correctamente"}), 200
