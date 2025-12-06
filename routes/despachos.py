from flask import Blueprint, app, request, jsonify
from extensions import db
from models.despachos import Despacho
from models.turnos import Turno
from models.clientes import Cliente
from models.conductores import Conductor
from models.autos import Auto
from datetime import datetime
from utils.auth import rol_requerido
from flask import render_template
from datetime import datetime, timezone

despachos_bp = Blueprint("despachos", __name__, url_prefix="/despachos")
@despachos_bp.route("/", methods=["POST"])
def crear_despacho():
    data = request.get_json()

    # 🔹 Capturar los campos con los nombres correctos
    origen = data.get("origen_despacho")
    destino = data.get("destino_despacho")
    cliente_id = data.get("cliente_id")
    conductor_id = data.get("conductor_id")
    auto_id = data.get("auto_id")
    tarifa = data.get("tarifa")
    estado = data.get("estado_despacho", "en curso")

    # 🔹 Validación rápida
    if not origen or not destino:
        return jsonify({"error": "Origen y destino son obligatorios"}), 400

    # 🔹 Crear el despacho
    nuevo_despacho = Despacho(
        origen_despacho=origen,
        destino_despacho=destino,
        cliente_id=cliente_id,
        conductor_id=conductor_id,
        auto_id=auto_id,
        tarifa=tarifa,
        estado_despacho=estado,
        fecha_hora_inicio=datetime.now()
    )

    db.session.add(nuevo_despacho)

    # 🔹 Cambiar estado del conductor a Ocupado
    if nuevo_despacho.conductor:
        nuevo_despacho.conductor.estado = "Ocupado"
    
    # 🔹 Si viene de lista de espera, marcar como finalizado
    lista_espera_id = data.get("lista_espera_id")
    if lista_espera_id:
        cliente_espera = ListaEspera.query.get(lista_espera_id)
        if cliente_espera:
            cliente_espera.estado = "finalizado"
            db.session.add(cliente_espera)
    db.session.commit()

    return jsonify({
        "msg": "Despacho creado",
        "id_despacho": nuevo_despacho.id_despacho,
        "conductor_estado": nuevo_despacho.conductor.estado if nuevo_despacho.conductor else None,
        "despacho": {
            "id_despacho": nuevo_despacho.id_despacho,
            "cliente_id": nuevo_despacho.cliente_id,
            "conductor_id": nuevo_despacho.conductor_id,
            "auto_id": nuevo_despacho.auto_id,
            "origen_despacho": nuevo_despacho.origen_despacho,
            "destino_despacho": nuevo_despacho.destino_despacho,
            "tarifa": nuevo_despacho.tarifa,
            "estado_despacho": nuevo_despacho.estado_despacho,
            "fecha_hora_inicio": nuevo_despacho.fecha_hora_inicio,
            "fecha_hora_fin": nuevo_despacho.fecha_hora_fin
        }
    }), 201




@despachos_bp.route("/", methods=["GET"])
def listar_despachos():
    despachos = Despacho.query.all()
    resultado = [
        {
            "id_despacho": d.id_despacho,
            "origen": d.origen_despacho,
            "destino": d.destino_despacho,
            "cliente": {"id": d.cliente.id_cliente, "nombre": d.cliente.nombre},
            "conductor": {"id": d.conductor.id_conductor, "nombre": d.conductor.nombre},
            "auto": {"id": d.auto.id_auto, "placa": d.auto.nro_placa},
            "tarifa": d.tarifa,
            "estado": d.estado_despacho
        }
        for d in despachos
    ]
    return jsonify(resultado), 200

@despachos_bp.route("/<int:id>", methods=["GET"])
def obtener_despacho(id):
    despacho = Despacho.query.get_or_404(id)
    return jsonify({
        "id_despacho": despacho.id_despacho,
        "origen": despacho.origen_despacho,
        "destino": despacho.destino_despacho,
        "cliente": {"id": despacho.cliente.id_cliente, "nombre": despacho.cliente.nombre},
        "conductor": {"id": despacho.conductor.id_conductor, "nombre": despacho.conductor.nombre},
        "auto": {"id": despacho.auto.id_auto, "placa": despacho.auto.nro_placa},
        "tarifa": despacho.tarifa,
        "estado": despacho.estado_despacho
    })


@despachos_bp.route("/<int:id>", methods=["PUT"])
def actualizar_despacho(id):
    despacho = Despacho.query.get_or_404(id)
    data = request.get_json()

    # Actualizar estado si viene en el JSON
    if "estado" in data:
        despacho.estado_despacho = data["estado"]

        # Si el estado es "finalizado", asignar fecha_hora_fin
        if data["estado"] == "finalizado":
            despacho.fecha_hora_fin = datetime.now()

    db.session.commit()

    return jsonify({
        "msg": "Despacho actualizado",
        "id_despacho": despacho.id_despacho,
        "estado": despacho.estado_despacho,
        "fecha_hora_inicio": despacho.fecha_hora_inicio.isoformat() if despacho.fecha_hora_inicio else None,
        "fecha_hora_fin": despacho.fecha_hora_fin.isoformat() if despacho.fecha_hora_fin else None
    }), 200
@despachos_bp.route("/inicializar_demo", methods=["POST"])
def inicializar_datos_demo():
    # =========================
    # CLIENTE DEMO
    # =========================
    if not Cliente.query.filter_by(telefono="04141234567").first():
        cliente = Cliente(
            telefono="04141234567",
            nombre="Cliente Demo",
            direccion="Av. Principal #123"
        )
        db.session.add(cliente)
        db.session.commit()

    # =========================
    # CONDUCTOR DEMO
    # =========================
    if not Conductor.query.filter_by(cod_conductor="C001").first():
        conductor = Conductor(
            cod_conductor="C001",
            nombre="Conductor Demo",
            nro_telefono="04149876543"
        )
        db.session.add(conductor)
        db.session.commit()

    # =========================
    # AUTO DEMO
    # =========================
    if not Auto.query.filter_by(nro_placa="ABC123").first():
        auto = Auto(
            nro_placa="ABC123",
            tipo_auto="Sedán",
            marca="Toyota",
            modelo="Corolla"
        )
        db.session.add(auto)
        db.session.commit()

    # =========================
    # DESPACHO DEMO
    # =========================
    cliente = Cliente.query.filter_by(telefono="04141234567").first()
    conductor = Conductor.query.filter_by(cod_conductor="C001").first()
    auto = Auto.query.filter_by(nro_placa="ABC123").first()

    if not Despacho.query.filter_by(cliente_id=cliente.id_cliente).first():
        despacho = Despacho(
            fecha_hora_inicio=datetime.now(),
            origen_despacho="Terminal",
            destino_despacho="Centro",
            cliente_id=cliente.id_cliente,
            conductor_id=conductor.id_conductor,
            auto_id=auto.id_auto,
            tarifa=10.0,
            estado_despacho="en curso"
        )
        db.session.add(despacho)
        db.session.commit()

    return jsonify({"msg": "Datos iniciales creados"}), 201

@despachos_bp.route("/<int:id>", methods=["DELETE"])
def eliminar_despacho(id):
    despacho = Despacho.query.get_or_404(id)
    db.session.delete(despacho)
    db.session.commit()
    return jsonify({
        "msg": "Despacho eliminado",
        "id_despacho": id
    }), 200

@despachos_bp.route("/<int:id>", methods=["DELETE"])
@rol_requerido(["admin"])   # solo admin puede eliminar
def candelar_despacho(id):
    despacho = Despacho.query.get_or_404(id)
    db.session.delete(despacho)
    db.session.commit()
    return jsonify({"msg": "Despacho eliminado", "id_despacho": id}), 200

@despachos_bp.route("/activos", methods=["GET"])
def listar_despachos_activos():
    # 🔹 Solo despachos en curso
    despachos = Despacho.query.filter_by(estado_despacho="en curso").all()
    resultado = []
    for d in despachos:
        resultado.append({
            "id_despacho": d.id_despacho,
            "cliente_telefono": d.cliente.telefono if d.cliente else "-",
            "cliente_nombre": d.cliente.nombre if d.cliente else "-",
            "conductor_nombre": d.conductor.nombre if d.conductor else "-",
            "auto_placa": d.auto.nro_placa if d.auto else "-",
            "origen": d.origen_despacho,
            "destino": d.destino_despacho,
            "tarifa": d.tarifa,
            "estado_despacho": d.estado_despacho
        })
    return jsonify(resultado), 200


@despachos_bp.route("/<int:id>/finalizar", methods=["PUT"])
def finalizar_despacho(id):
    try:
        despacho = Despacho.query.get_or_404(id)
        despacho.estado_despacho = "finalizado"
        despacho.fecha_hora_fin = datetime.now(timezone.utc)

        # 🔹 No cerramos el turno aquí
       # conductor = Conductor.query.get(despacho.conductor_id)
       # if conductor:
       #     conductor.estado = "activo"

        db.session.commit()

        return jsonify({
            "msg": "Despacho finalizado correctamente",
            "id_despacho": despacho.id_despacho,
            "fecha_hora_fin": despacho.fecha_hora_fin.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al finalizar despacho: {str(e)}"}), 500



@despachos_bp.route("/<int:id>/cancelar", methods=["PUT"])
def cancelar_despacho(id):
    despacho = Despacho.query.get_or_404(id)
    despacho.estado_despacho = "cancelado"
    db.session.commit()
    return jsonify(despacho.to_dict())

