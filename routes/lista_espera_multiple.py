from flask import Blueprint, request, jsonify
from extensions import db
from models import ListaEsperaMultiple, Cliente

lista_espera_multiple_bp = Blueprint("lista_espera_multiple", __name__)

# GET → listar cola con datos del cliente
@lista_espera_multiple_bp.route("/api/cola_multiple", methods=["GET"])
def listar_cola_multiple():
    registros = ListaEsperaMultiple.query.join(Cliente).filter(ListaEsperaMultiple.estado == "EN_ESPERA_MULTIPLE").all()
    return jsonify([
        {
            "id_lista_multiple": r.id_lista_multiple,
            "cliente_id": r.cliente_id,
            "telefono": r.cliente.telefono,
            "nombre": r.cliente.nombre,
            "direccion": r.cliente.direccion,
            "iteraciones": r.iteraciones,
            "estado": r.estado
        }
        for r in registros
    ]), 200

# POST → crear nuevo registro en cola
@lista_espera_multiple_bp.route("/api/cola_multiple", methods=["POST"])
def crear_cola_multiple():
    data = request.get_json()
    try:
        nuevo = ListaEsperaMultiple(
            cliente_id=data.get("id_cliente"),
            iteraciones=data.get("iteraciones"),
            estado=data.get("estado", "en espera")
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({"status": "ok", "registro": {
            "id_lista_multiple": nuevo.id_lista_multiple,
            "cliente_id": nuevo.cliente_id,
            "iteraciones": nuevo.iteraciones,
            "estado": nuevo.estado
        }}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 400

@lista_espera_multiple_bp.route("/api/despacho_multiple/<int:idCola>", methods=["POST"])
def mover_a_despacho_multiple(idCola):
    data = request.get_json()
    iteraciones = data.get("iteraciones")

    registro = ListaEsperaMultiple.query.get(idCola)
    if not registro:
        return jsonify({"status": "error", "mensaje": "Registro no encontrado"}), 404

    registro.estado = "ASIGNADO"
    registro.iteraciones = iteraciones
    db.session.commit()

    return jsonify({"status": "ok", "mensaje": "Cliente movido a despacho múltiple"}), 200

