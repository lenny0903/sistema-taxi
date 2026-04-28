import re
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.clientes import Cliente
from models.despachos import Despacho
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError 
from datetime import datetime
from sqlalchemy import text
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
    
    if not telefono or not validar_telefono(telefono):
        return jsonify({"error": "Teléfono inválido o ausente"}), 400

    nombre = (data.get('nombre') or "").strip()
    if not validar_nombre(nombre):
        return jsonify({"error": "Nombre inválido"}), 400

    # 🔍 Buscamos si ya existe físicamente
    cliente_existente = Cliente.query.filter_by(telefono=telefono).first()

    if cliente_existente:
        if cliente_existente.estado == 1:
            return jsonify({"error": "Teléfono ya registrado y activo"}), 400
        
        # 🔄 RECTIVACIÓN: Si estaba en 0, lo tratamos como "limpieza de datos"
        # Sobrescribimos todo para cumplir la regla del 2026-01-13
        cliente_existente.nombre = nombre
        cliente_existente.direccion = data.get('direccion')
        cliente_existente.punto_referencia = (data.get('punto_referencia') or "").strip() or None
        cliente_existente.estado = 1 
        db.session.commit()
        return jsonify({"message": "Cliente reactivado con nueva información", "id_cliente": cliente_existente.id_cliente}), 200

    # ✨ CREACIÓN DESDE CERO
    nuevo_cliente = Cliente(
        nombre=nombre,
        telefono=telefono,
        direccion=data.get('direccion'),
        punto_referencia=(data.get('punto_referencia') or "").strip() or None,
        estado=1
    )
    db.session.add(nuevo_cliente)
    db.session.commit()
    return jsonify({"message": "Cliente creado", "id_cliente": nuevo_cliente.id_cliente}), 201


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


# Listar clientes (Optimizado para 40k registros)
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    page = request.args.get('page', 1, type=int) # Recibe la página de la URL
    per_page = 50 # Registros por vista
    
    # paginate hace todo: cuenta el total, calcula los saltos, etc.
    p = Cliente.query.filter_by(estado=1).order_by(Cliente.id_cliente.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        "clientes": [
            {
                "id_cliente": c.id_cliente,
                "nro_telefono": c.telefono,
                "nombre": c.nombre,
                "direccion": c.direccion,
                "punto_referencia": c.punto_referencia
            } for c in p.items
        ],
        "total_paginas": p.pages,
        "pagina_actual": p.page,
        "total_registros": p.total
    }), 200

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
        # 🔥 AGREGAMOS EL FILTRO DE ESTADO ACTIVO
        cliente = Cliente.query.filter(
            Cliente.telefono == telefono, 
            Cliente.estado == 1
        ).all()
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

@clientes_bp.route('/<int:id_cliente>', methods=['DELETE'])
@jwt_required()
def eliminar_o_desactivar(id_cliente):
    cliente = Cliente.query.get_or_404(id_cliente)
    responsable_id = get_jwt_identity()
    
    try:
        # 🔍 Contamos cuántos despachos tiene para informar al operador
        sql_count = text("SELECT COUNT(*) FROM despachos WHERE cliente_id = :id")
        cantidad_pedidos = db.session.execute(sql_count, {"id": id_cliente}).scalar()
        
        tiene_historial = cantidad_pedidos > 0

        if not tiene_historial:
            # 🗑️ ES BASURA: Borrado físico real
            try:
                nombre_cliente = cliente.nombre
                db.session.delete(cliente)
                db.session.commit()
                return jsonify({
                    "mensaje": f"El cliente '{nombre_cliente}' no tenía historial y ha sido ELIMINADO permanentemente del sistema."
                }), 200
            except Exception:
                db.session.rollback()
                tiene_historial = True # Fallo técnico, procedemos a desactivar

        if tiene_historial:
            # 👁️‍🗨️ ES HISTÓRICO: Borrado lógico
            cliente.estado = 0
            cliente.usuario_id_auditoria = responsable_id
            cliente.fecha_modificacion = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "mensaje": f"El cliente '{cliente.nombre}' tiene {cantidad_pedidos} despachos asociados. Se ha DESACTIVADO para proteger el historial contable."
            }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error crítico en eliminación: {str(e)}")
        return jsonify({"error": "Error interno al procesar la eliminación."}), 500
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

    try:
        cliente.telefono = nuevo_tel
        db.session.commit() 
        return jsonify({"message": "Teléfono actualizado correctamente"}), 200
    except IntegrityError:
        db.session.rollback() 
        # Mensaje súper amigable
        return jsonify({"error": "No se puede guardar: este número de teléfono ya está asignado a otro cliente."}), 400
    except Exception as e:
        db.session.rollback()
        #Evita enviar el {str(e)} al usuario, solo regístralo en consola del servidor
        print(f"DEBUG ERROR: {str(e)}") 
        return jsonify({"error": "Hubo un problema técnico en el servidor. Intente más tarde."}), 500
# 🔹 Buscar clientes por nombre o teléfono (Server-side)
@clientes_bp.route('/search', methods=['GET'])
def buscar_clientes_full():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([]), 200

    # El SSD del i5 hará que este filtro sea instantáneo
    # Buscamos coincidencias en nombre O en teléfono
    resultados = Cliente.query.filter(
        Cliente.estado == 1, # <--- Esta es la llave de seguridad
        (Cliente.nombre.ilike(f"%{query}%") | Cliente.telefono.ilike(f"%{query}%"))
    ).limit(20).all()

    return jsonify([
        {
            "id_cliente": c.id_cliente,
            "nro_telefono": c.telefono,
            "nombre": c.nombre,
            "direccion": c.direccion,
            "punto_referencia": c.punto_referencia
        }
        for c in resultados
    ]), 200

# Ruta para actualizar un cliente específico por su ID
@clientes_bp.route('/<int:id_cliente>', methods=['PUT'])
def actualizar_cliente_id(id_cliente):
    # Obtiene el cliente o lanza 404 si no existe
    cliente = Cliente.query.get_or_404(id_cliente)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    try:
        # Actualizamos solo los campos que vengan en el JSON
        if "nombre" in data:
            cliente.nombre = data["nombre"].strip()
        
        if "direccion" in data:
            cliente.direccion = data["direccion"].strip()
            
        if "telefono" in data:
            cliente.telefono = data["telefono"].strip()

        db.session.commit()
        
        return jsonify({
            "mensaje": "Cliente actualizado con éxito",
            "cliente": {
                "id_cliente": cliente.id_cliente,
                "nombre": cliente.nombre,
                "direccion": cliente.direccion
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar: {str(e)}"}), 500