import uuid
import json
import os
import sqlite3  
from engineio import payload
from flask import Blueprint, app, request, jsonify
from extensions import db
from models.cola_notificaciones import ColaNotificaciones
from models import despachos
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
from utils.notificaciones import enviar_encuesta_satisfaccion

def hora_local():
    return datetime.now(ZoneInfo("America/Caracas"))
from models.lista_espera import ListaEspera
despachos_bp = Blueprint("despachos", __name__, url_prefix="/despachos")

from models.incidencias import BloqueoAfinidad # ⬅️ Importamos el modelo de bloqueos

@despachos_bp.route("/", methods=["POST"])
def crear_despacho():
    try:
        data = request.get_json()
        print(f"DEBUG: Contenido total recibido del frontend: {data}")
        
        # 1. Extraer y validar
        origen = data.get("origen_despacho")
        cliente_id = data.get("cliente_id")
        conductor_id = data.get("conductor_id")

        if not origen:
            return jsonify({"error": "El origen es obligatorio"}), 400

        if not cliente_id or not conductor_id:
            return jsonify({"error": "Cliente y conductor son obligatorios"}), 400

        try:
            tarifa_val = float(data.get("tarifa", 0))
        except:
            tarifa_val = 0.0

        # ====================================================================
        # 🚨 VALIDACIÓN BACKEND: Evitar el despacho si hay exclusión activa
        # ====================================================================
        bloqueo = BloqueoAfinidad.query.filter_by(
            cliente_id=cliente_id,
            conductor_id=conductor_id,
            tipo_bloqueo="CONDUCTOR_EXCLUSION",
            activo=True
        ).first()

        if bloqueo:
            return jsonify({
                "error": f"Bloqueo activo: El conductor no puede atender a este cliente. Motivo: {bloqueo.nota_gerencial}"
            }), 400
        # ====================================================================

       # --- USAMOS NO_AUTOFLUSH PARA EVITAR EL ERROR ---
        with db.session.no_autoflush:
            ahora = hora_local()
            nuevo_despacho = Despacho(
                origen_despacho=origen,
                destino_despacho=data.get("destino_despacho"),
                cliente_id=cliente_id,
                conductor_id=conductor_id,
                auto_id=data.get("auto_id"),
                tarifa=tarifa_val,
                estado_despacho=data.get("estado_despacho", "en curso"),
                fecha_hora_inicio=ahora,
                fecha_hora_embarque=ahora,
                grupo_id=data.get("grupo_id")
            )
            db.session.add(nuevo_despacho)
            db.session.flush() # Genera el ID del nuevo despacho
            
            # --- OBTENCIÓN SEGURA DE DATOS ---
            cliente_obj = Cliente.query.get(cliente_id)
            conductor_obj = Conductor.query.get(conductor_id)
            
            c_tel = data.get("cliente_telefono") or (cliente_obj.telefono if cliente_obj else "0000000")
            c_nom = cliente_obj.nombre if cliente_obj else "Cliente"
            con_tel = data.get("conductor_telefono") or (conductor_obj.nro_telefono if conductor_obj else "0000000")
            con_nom = conductor_obj.nombre if conductor_obj else "Conductor"
            con_cod = conductor_obj.codigo if conductor_obj else "S/C"

            # ====================================================================
            # 🛡️ VALIDACIÓN DE VIGENCIA DEL CONDUCTOR PARA EL ENLACE/NOTIFICACIÓN
            # ====================================================================
            conductor_valido = True
            if not conductor_obj:
                conductor_valido = False
            else:
                # Normalizar la expiración del GPS para evitar choques de zonas horarias
                exp_gps = conductor_obj.expiracion_gps
                if exp_gps and exp_gps.tzinfo is None and ahora.tzinfo is not None:
                    exp_gps = exp_gps.replace(tzinfo=ahora.tzinfo)

                # Validación segura única
                if conductor_obj.estado_red != 'conectado' or (exp_gps and exp_gps < ahora):
                    conductor_valido = False
                    print(f"⚠️ [ALERTA] Despacho #{nuevo_despacho.id_despacho} creado, pero el conductor {con_cod} está inactivo o con GPS expirado. No se generará el enlace automático.")

            # Solo construimos la notificación y el enlace si el conductor es válido
            if conductor_valido:
                codigo_minicla = con_cod.lower()
                url_flayer = f"/home/lenny/.n8n-files/{con_cod.lower()}.png"
                
                escenario_final = "CON_WHATSAPP" if c_tel.startswith('04') else "SIN_WHATSAPP"
                
                payload = {
                    "turno_id": nuevo_despacho.id_despacho,
                    "escenario": escenario_final,
                    "cliente": {
                        "nombre": c_nom, 
                        "telefono": c_tel
                    },
                    "conductor": {
                        "nombre": con_nom, 
                        "telefono": con_tel,
                        "codigo": con_cod
                    },
                    "servicio": {
                        "origen": origen, 
                        "destino": data.get("destino_despacho"), 
                        "tarifa": tarifa_val,
                        "flayer_url": url_flayer
                    }
                }
                
                notificacion = ColaNotificaciones(
                    turno_id=nuevo_despacho.id_despacho,
                    tipo_mensaje='DESPACHO_AUTOMATICO',
                    destinatario_telefono=str(c_tel),
                    contenido_json=json.dumps(payload),
                    estado='PENDIENTE'
                )
                db.session.add(notificacion)
            
            # Borrado de Cola (si aplica)
            cola_id = data.get("id_notificacion")
            if cola_id:
                db.session.query(ColaDespacho).filter_by(id_cola=cola_id).delete(synchronize_session=False)

        db.session.commit()

        # Respuesta indicando el estado del despacho y si se encoló el mensaje
        mensaje_respuesta = "Despacho creado exitosamente"
        if not conductor_valido:
            mensaje_respuesta += " (⚠️ Advertencia: Conductor inactivo o GPS expirado, no se generó enlace de WhatsApp)."

        return jsonify({
            "msg": mensaje_respuesta,
            "id_despacho": nuevo_despacho.id_despacho,
            "cliente_telefono": c_tel,
            "enlace_generado": conductor_valido
        }), 201

    except Exception as e:
        db.session.rollback()
        print("❌ Error en DB:", str(e))
        return jsonify({"error": "Error interno: " + str(e)}), 500
        
@despachos_bp.route("/", methods=["GET"])
def obtener_despacho(id):
    # 1. Obtenemos el despacho específico por su ID
    d = Despacho.query.get_or_404(id)
    
    # 2. Retornamos directamente el diccionario con los datos
    return jsonify({
        'id_despacho': d.id_despacho,
        'auto_placa': d.auto_placa,
        'destino': d.destino,
        'origen': d.origen,
        'tarifa': d.tarifa,
        'estado_despacho': d.estado_despacho,
        'cliente_nombre': d.cliente.nombre if d.cliente else "N/D",
        'cliente_telefono': d.cliente.telefono if d.cliente else "N/D",
        'conductor_nombre': d.conductor.nombre if d.conductor else "N/D",
        
        # ⚠️ Los IDs que el frontend necesita desesperadamente:
        'cliente_id': d.id_cliente, 
        'id_cliente': d.id_cliente,
        'conductor_id': d.id_conductor,
        'id_conductor': d.id_conductor
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
    try:
        # 🔹 Corregido: Buscamos tanto los que están 'en curso' como los 'notificado'
        despachos = Despacho.query.filter_by(estado_despacho="en curso").all()
        resultado = []
        
        for d in despachos:
            # 1. Extraer ID del cliente con seguridad
            c_id = None
            if d.cliente:
                c_id = getattr(d.cliente, 'id_cliente', getattr(d.cliente, 'id', None))
            
            # 2. Extraer ID del conductor con seguridad
            cond_id = None
            if d.conductor:
                cond_id = getattr(d.conductor, 'id_conductor', getattr(d.conductor, 'id', None))

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
                
                # IDs extraídos con total seguridad para el frontend:
                "cliente_id": c_id,
                "conductor_id": cond_id
            })
            
        return jsonify(resultado), 200

    except Exception as e:
        print(f"❌ Error en listar_despachos_activos: {str(e)}")
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

@despachos_bp.route("/<int:id>/finalizar", methods=["PUT"])
def finalizar_despacho(id):
    try:
        despacho = Despacho.query.get_or_404(id)
        print(f"DEBUG: Despacho {id} - Embarque original: {despacho.fecha_hora_embarque}")
        # ✅ Si no tiene hora de embarque, la asignamos ahora mismo (automático)
        if not despacho.fecha_hora_embarque:
            despacho.fecha_hora_embarque = hora_local()

        # 🚨 Validar que tenga auto asignado (Esta sí la dejamos por seguridad)
        if not despacho.auto_id:
            return jsonify({"error": "No se puede finalizar un despacho sin auto asignado"}), 400

        despacho.estado_despacho = "finalizado"
        despacho.fecha_hora_fin = hora_local()

        db.session.commit()
       
        # Se verifica que exista y que no esté vacío antes de intentar el envío
       # 🟢 ENVÍO SEGURO DE ENCUESTA POR TELEGRAM
        telegram_cliente = getattr(despacho, 'telegram_id_cliente', None)

        if telegram_cliente and str(telegram_cliente).strip():
            try:
                enviar_encuesta_satisfaccion(
                    telegram_cliente,      # Posición 1: chat_id_cliente
                    despacho.id_despacho   # Posición 2: id_despacho
                )
            except Exception as e_tg:
                print(f"⚠️ No se pudo enviar la encuesta vía Telegram al cliente {telegram_cliente}: {e_tg}")
        else:
            print(f"ℹ️ Despacho #{despacho.id_despacho} finalizado sin Telegram (Cliente presencial o vía telefónica).")
        return jsonify({
            "msg": "Despacho finalizado correctamente",
            "id_despacho": despacho.id_despacho,
            "auto_id": despacho.auto_id,
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



def registrar_notificacion_despacho(turno, cliente_telefono, conductor_telefono):
    # Preparamos el payload que n8n va a recibir
    payload = {
        "turno_id": turno.id,
        "cliente": {"nombre": turno.cliente_nombre, "telefono": cliente_telefono},
        "conductor": {"nombre": turno.conductor_nombre, "telefono": conductor_telefono},
        "servicio": {"origen": turno.origen, "destino": turno.destino, "tarifa": float(turno.tarifa)}
    }
    
    # Creamos la orden en la cola
    nueva_notificacion = ColaNotificaciones(
        turno_id=turno.id,
        tipo_mensaje='DESPACHO_AUTOMATICO',
        destinatario_telefono=cliente_telefono, # O conductor, según prefieras
        contenido_json=json.dumps(payload),
        estado='PENDIENTE'
    )
    
    db.session.add(nueva_notificacion)
    db.session.commit()

@despachos_bp.route('/webhook/status_whatsapp', methods=['POST'])
def status_whatsapp():
    datos = request.json
    print("📝 Datos recibidos desde n8n:", datos)

    id_viaje = datos.get('turno_id')
    estado = datos.get('status') 
    error_msg = datos.get('error', 'Sin detalles')

    try:
        # 🚖 Buscamos el despacho usando SQLAlchemy (Evita choques de archivos .db)
        despacho_obj = Despacho.query.get(id_viaje)
        
        if despacho_obj:
            if estado == 'fallido':
                print(f"🚨 ALERTA: El flayer para el viaje {id_viaje} NO se envió. Motivo: {error_msg}")
                despacho_obj.estado_despacho = 'fallido'
            else:
                print(f"✅ CONFIRMACIÓN: El flayer para el viaje {id_viaje} fue enviado con éxito.")
                # Si quieres que siga saliendo en tu tabla que busca 'en curso', déjalo 'en curso'
                # despacho_obj.estado_despacho = 'en curso' 
                
                # O si prefieres dejarlo como 'notificado', recuerda activar el .in_() en /activos
                despacho_obj.estado_despacho = 'notificado'
            
            db.session.commit()
            print(f"💾 Estado del despacho {id_viaje} actualizado con éxito en SQLAlchemy.")
        else:
            print(f"⚠️ No se encontró el despacho con ID {id_viaje} en la BD.")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error actualizando estatus en webhook: {e}")
    
    return jsonify({"status": "recibido", "msg": "Estatus procesado"}), 200