# routes/lista_espera.py
from flask import Blueprint, request, jsonify
from extensions import db
from models.lista_espera import ListaEspera
from datetime import datetime
from utils.time import hora_local

lista_espera_bp = Blueprint("lista_espera", __name__, url_prefix="/lista_espera")



@lista_espera_bp.route("/<int:id>", methods=["DELETE"])
def eliminar_lista_espera(id):
    cliente = ListaEspera.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({"msg": "Cliente eliminado de lista de espera"}), 200

@lista_espera_bp.route("/<int:id>", methods=["GET"])
def obtener_cliente_espera(id):
    cliente = ListaEspera.query.get_or_404(id)
    return jsonify(cliente.to_dict()), 200

@lista_espera_bp.route("/", methods=["GET", "POST"])
def lista_espera():
    if request.method == "GET":
        lista = ListaEspera.query.all()
        return jsonify([l.to_dict() for l in lista]), 200

    elif request.method == "POST":
        data = request.get_json()
        print("🚦 Payload recibido:", data)

        hora_str = data.get("hora")
        try:
            hora = hora_local()
        except ValueError:
            try:
                hora = hora_local()
            except ValueError:
                # último recurso: interpretar como ISO estándar
                hora = datetime.fromisoformat(hora_str.replace("Z", "+00:00"))

        # Ajustar a zona local Venezuela (UTC-4)
        from datetime import timezone, timedelta
        hora = hora.astimezone(timezone(timedelta(hours=-4)))

        nuevo = ListaEspera(
            cliente_id=data.get("cliente_id"),
            origen=data.get("origen"),
            destino=data.get("destino"),
            hora=hora,
            nro_telefono=data.get("nro_telefono"),
            estado=data.get("estado", "en espera"),
            tarifa=data.get("tarifa"),
        )
        
        db.session.add(nuevo)
        db.session.commit()
        return jsonify(nuevo.to_dict()), 201

