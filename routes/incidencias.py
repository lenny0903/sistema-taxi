from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from datetime import datetime, timezone
from models.incidencias import Incidencia, BloqueoAfinidad

# Asegúrate de importar también tus modelos de Cliente y Conductor si los usas
incidencias_bp = Blueprint('incidencias', __name__)

# 🔹 1. REGISTRAR UNA INCIDENCIA CON LA REGLA DE LA ADMINISTRADORA
@incidencias_bp.route('/', methods=['POST'])  # ⬅️ Usa "/" en lugar de "/incidencias"
@jwt_required()
def crear_incidencia():
    try:
        data = request.get_json()
        operador_id = get_jwt_identity()

        despacho_id = data.get("despacho_id")
        cliente_id = data.get("cliente_id")
        conductor_id = data.get("conductor_id")
        categoria = data.get("categoria")          # Ej: 'CLIENTE_EBRIO', 'COBRO_EXCESIVO', etc.
        origen_reporte = data.get("origen_reporte") # 'CLIENTE' o 'CONDUCTOR'
        descripcion = data.get("descripcion")

        if not cliente_id or not categoria or not descripcion or not origen_reporte:
            return jsonify({"error": "Faltan campos obligatorios"}), 400

        # A. Crear el registro de la incidencia en el historial
        nueva_incidencia = Incidencia(
            despacho_id=despacho_id,
            cliente_id=cliente_id,
            conductor_id=conductor_id,
            categoria=categoria.upper(),
            descripcion=descripcion,
            operador_id=operador_id
        )
        db.session.add(nueva_incidencia)

        # ====================================================================
        # 🚨 LA REGLA DE LA ADMINISTRADORA:
        # ====================================================================
        
        # Escenario 1: Si el origen es CONDUCTOR, se genera exclusión mutua automática
        if origen_reporte.upper() == "CONDUCTOR" and conductor_id:
            bloqueo = BloqueoAfinidad(
                cliente_id=cliente_id,
                conductor_id=conductor_id,
                tipo_bloqueo="CONDUCTOR_EXCLUSION",
                activo=True,
                nota_gerencial=f"Exclusión reportada por conductor: {descripcion[:150]}",
                fecha_creacion=datetime.now(timezone.utc)
            )
            db.session.add(bloqueo)

        # Escenario 2: El cliente no pagó la carrera (VETO GENERAL)
        elif categoria.upper() == "NO_PAGO":
            bloqueo = BloqueoAfinidad(
                cliente_id=cliente_id,
                conductor_id=None,  # Veto general
                tipo_bloqueo="CLIENTE_GENERAL",
                activo=True,
                nota_gerencial=f"VETO POR INCUMPLIMIENTO DE PAGO: {descripcion[:150]}",
                fecha_creacion=datetime.now(timezone.utc)
            )
            db.session.add(bloqueo)

        # Escenario 3: Cliente reportó mala experiencia con el conductor (Opcional, también se excluyen)
        elif origen_reporte.upper() == "CLIENTE" and conductor_id and categoria.upper() != "NO_PAGO":
            bloqueo = BloqueoAfinidad(
                cliente_id=cliente_id,
                conductor_id=conductor_id,
                tipo_bloqueo="CONDUCTOR_EXCLUSION",
                activo=True,
                nota_gerencial=f"Exclusión reportada por cliente: {descripcion[:150]}",
                fecha_creacion=datetime.now(timezone.utc)
            )
            db.session.add(bloqueo)

        db.session.commit()
        return jsonify({"msg": "Incidencia y restricciones registradas correctamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 🔹 2. VALIDAR CLIENTE (Veto General)
@incidencias_bp.route('/validar_cliente/<int:cliente_id>', methods=['GET'])
@jwt_required()
def validar_cliente(cliente_id):
    try:
        bloqueo = BloqueoAfinidad.query.filter_by(
            cliente_id=cliente_id,
            tipo_bloqueo="CLIENTE_GENERAL",
            activo=True
        ).first()

        if bloqueo:
            return jsonify({
                "bloqueado": True,
                "mensaje": f"⚠️ ALERTA: Cliente Vetado. {bloqueo.nota_gerencial}"
            }), 200

        return jsonify({"bloqueado": False, "mensaje": "Cliente sin restricciones"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 3. VALIDAR AFINIDAD (Exclusión mutua entre Conductor y Cliente)
@incidencias_bp.route('/validar_afinidad', methods=['POST'])
@jwt_required()
def validar_afinidad():
    try:
        data = request.get_json()
        cliente_id = data.get("cliente_id")
        conductor_id = data.get("conductor_id")

        if not cliente_id or not conductor_id:
            return jsonify({"error": "Faltan parámetros"}), 400

        bloqueo = BloqueoAfinidad.query.filter_by(
            cliente_id=cliente_id,
            conductor_id=conductor_id,
            tipo_bloqueo="CONDUCTOR_EXCLUSION",
            activo=True
        ).first()

        if bloqueo:
            return jsonify({
                "permitido": False,
                "mensaje": f"🚫 EXCLUSIÓN: El conductor no puede atender a este cliente. Motivo: {bloqueo.nota_gerencial}"
            }), 200

        return jsonify({"permitido": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidencias_bp.route('/verificar_cliente/<int:cliente_id>', methods=['GET'])
@jwt_required() # Déjalo si usas token, o quítalo si no lo necesitas
def verificar_cliente(cliente_id):
    try:
        # 1. Buscar si tiene un veto explícito en la tabla de bloqueos
        veto = BloqueoAfinidad.query.filter_by(
            cliente_id=cliente_id,
            tipo_bloqueo="CLIENTE_GENERAL",
            activo=True
        ).first()

        if veto:
            return jsonify({
                "tiene_veto_general": True,
                "mensaje_veto": veto.nota_gerencial,
                "tiene_exclusiones": False
            }), 200

        # 2. 🚨 ¡NUEVA REGLA DE RESPALDO!: Buscar directamente en la tabla de incidencias
        # Si tiene alguna incidencia de categoría grave, lo vetamos de inmediato.
        incidencia_grave = Incidencia.query.filter(
            Incidencia.cliente_id == cliente_id,
            Incidencia.categoria.in_(["CLIENTE_EBRIO", "NO_PAGO", "VIOLENCIA", "AGRESIÓN"])
        ).order_by(Incidencia.id.desc()).first()

        if incidencia_grave:
            return jsonify({
                "tiene_veto_general": True,
                "mensaje_veto": f"Reporte de {incidencia_grave.categoria}: {incidencia_grave.descripcion}",
                "tiene_exclusiones": False
            }), 200

        # 3. ¿Tiene exclusiones de afinidad con conductores?
        exclusiones = BloqueoAfinidad.query.filter_by(
            cliente_id=cliente_id,
            tipo_bloqueo="CONDUCTOR_EXCLUSION",
            activo=True
        ).all()

        ultima_incidencia = Incidencia.query.filter_by(cliente_id=cliente_id).order_by(Incidencia.id.desc()).first()

        return jsonify({
            "tiene_veto_general": False,
            "tiene_exclusiones": len(exclusiones) > 0,
            "total_exclusiones": len(exclusiones),
            # 🎯 CORRECCIÓN: Agregamos la categoría real de la base de datos
            "categoria": ultima_incidencia.categoria if ultima_incidencia else "NOTA",
            "descripcion": ultima_incidencia.descripcion if ultima_incidencia else "Cliente sin reportes recientes."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500