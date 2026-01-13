import uuid
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
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from models.cola_despachos import ColaDespacho

def hora_local():
    return datetime.now(ZoneInfo("America/Caracas"))
from models.lista_espera import ListaEspera
despachos_bp = Blueprint("despachos", __name__, url_prefix="/despachos")

@despachos_bp.route("/", methods=["POST"])
def crear_despacho():
    try:
        data = request.get_json()
        
        # 1. Extraer y validar (Igual a como lo tienes)
        origen = data.get("origen_despacho")
        if not origen:
            return jsonify({"error": "El origen es obligatorio"}), 400

        try:
            tarifa_val = float(data.get("tarifa", 0))
        except:
            tarifa_val = 0.0

        # --- USAMOS NO_AUTOFLUSH PARA EVITAR EL ERROR ---
        with db.session.no_autoflush:
            # 2. Crear el objeto Despacho
            nuevo_despacho = Despacho(
                origen_despacho=origen,
                destino_despacho=data.get("destino_despacho"),
                cliente_id=data.get("cliente_id"),
                conductor_id=data.get("conductor_id"),
                auto_id=data.get("auto_id"),
                tarifa=tarifa_val,
                estado_despacho=data.get("estado_despacho", "en curso"),
                fecha_hora_inicio=datetime.now(),
                grupo_id=data.get("grupo_id")
            )
            db.session.add(nuevo_despacho)

            # 3. Borrado de Cola (Cambiamos el método para que sea atómico) 🔥
            cola_id = data.get("cola_id")
            if cola_id:
                # Usamos synchronize_session=False para que no intente validar la sesión antes de borrar
                db.session.query(ColaDespacho).filter_by(id_cola=cola_id).delete(synchronize_session=False)

        # 4. UN SOLO COMMIT FINAL
        db.session.commit()

        return jsonify({
            "msg": "Despacho creado",
            "id_despacho": nuevo_despacho.id_despacho
        }), 201

    except Exception as e:
        db.session.rollback()
        print("❌ Error en DB:", str(e))
        return jsonify({"error": "Error interno: " + str(e)}), 500

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
            "estado_despacho": d.estado_despacho,
            #"punto_referencia": d.cliente.punto_referencia if d.cliente else ""
        })
    return jsonify(resultado), 200


@despachos_bp.route("/<int:id>/finalizar", methods=["PUT"])
def finalizar_despacho(id):
    try:
        despacho = Despacho.query.get_or_404(id)

        # 🚨 Validar que tenga hora de embarque
        if not despacho.fecha_hora_embarque:
            return jsonify({"error": "No se puede finalizar un despacho sin hora de embarque"}), 400

        # 🚨 Validar que tenga auto asignado
        if not despacho.auto_id:
            return jsonify({"error": "No se puede finalizar un despacho sin auto asignado"}), 400

        despacho.estado_despacho = "finalizado"
        despacho.fecha_hora_fin = hora_local()

        db.session.commit()

        return jsonify({
            "msg": "Despacho finalizado correctamente",
            "id_despacho": despacho.id_despacho,
            "auto_id": despacho.auto_id,   # 👈 confirmación
            "fecha_hora_embarque": despacho.fecha_hora_embarque.isoformat(),
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

@despachos_bp.route("/<int:id>/embarque", methods=["PUT"])
def registrar_embarque(id):
    despacho = Despacho.query.get(id)
    if not despacho:
        return jsonify({"error": "Despacho no encontrado"}), 404

    despacho.fecha_hora_embarque = hora_local()
    db.session.commit()

    return jsonify({
        "id_despacho": despacho.id_despacho,
        "estado_despacho": despacho.estado_despacho,
        "fecha_hora_embarque": despacho.fecha_hora_embarque.isoformat()
    }), 200

@despachos_bp.route("/multiple", methods=["POST"])
def crear_despacho_multiple():
    data = request.get_json()
    print("📥 Datos recibidos en /despachos/multiple:", data)

    try:
        origen = data.get("origen_despacho")
        destino = data.get("destino_despacho")
        if not origen or not destino:
            return jsonify({"error": "Origen y destino son obligatorios"}), 400

        cliente_id = data.get("cliente_id")
        tarifa = data.get("tarifa", 0)
        estado = data.get("estado_despacho", "en curso")
        grupo_id = data.get("grupo_id")
        conductores_ids = data.get("conductores", [])

        if not conductores_ids:
            return jsonify({"error": "Debes indicar al menos un conductor"}), 400

        despachos_creados = []
        for conductor_id in conductores_ids:
            conductor = Conductor.query.get(conductor_id)
            if not conductor:
                continue

            auto = Auto.query.filter_by(conductor_id=conductor_id).first()

            nuevo_despacho = Despacho(
                origen_despacho=origen,
                destino_despacho=destino,
                cliente_id=cliente_id,
                conductor_id=conductor_id,
                auto_id=auto.id_auto if auto else None,
                tarifa=tarifa,
                estado_despacho=estado,
                fecha_hora_inicio=hora_local(),
                grupo_id=grupo_id
            )
            db.session.add(nuevo_despacho)
            despachos_creados.append(nuevo_despacho)

        db.session.commit()

        return jsonify({
            "msg": "Despachos múltiples creados",
            "despachos": [d.to_dict() for d in despachos_creados]
        }), 201

    except Exception as e:
        db.session.rollback()
        print("❌ Error creando despachos múltiples:", str(e))
        return jsonify({"error": str(e)}), 500



