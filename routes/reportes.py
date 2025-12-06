from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Despacho, Conductor
from app import db
from sqlalchemy import func
from flask import Blueprint, render_template
from flask import request
reporte_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reporte_bp.route('/conductor', methods=['GET'])
@jwt_required()
def reporte_por_conductor():
    resultados = db.session.query(
        Conductor.nombre,
        func.count(Despacho.id_despacho).label('total_servicios'),
        func.sum(Despacho.tarifa).label('total_tarifas')
    ).join(Despacho, Despacho.conductor_id == Conductor.id_conductor)\
     .filter(Despacho.estado_despacho == 'finalizado')\
     .group_by(Conductor.nombre).all()

    return jsonify([{
        "conductor": r[0],
        "total_servicios": r[1],
        "total_tarifas": float(r[2]) if r[2] else 0
    } for r in resultados])

@reporte_bp.route("/", methods=["GET"])
def reportes():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not inicio or not fin:
        return jsonify({"error": "Debes enviar inicio y fin"}), 400

    # Convertir a datetime
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d")

    # Filtrar por fecha de inicio
    despachos = (
        db.session.query(Despacho)
        .filter(Despacho.fecha_hora_inicio >= inicio_dt,
                Despacho.fecha_hora_inicio <= fin_dt)
        .all()
    )

    resultado = [
        {
            "id_despacho": d.id_despacho,
            "cliente_nombre": d.cliente.nombre,
            "conductor_nombre": d.conductor.nombre,
            "auto_placa": d.auto.nro_placa,
            "origen": d.origen_despacho,
            "destino": d.destino_despacho,
            "fecha": d.fecha_hora_inicio.strftime("%Y-%m-%d %H:%M"), 
            "tarifa": d.tarifa,
        }
        for d in despachos
    ]

    return jsonify(resultado)

@reporte_bp.route("/conductores", methods=["GET"])
def reportes_conductores():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not inicio or not fin:
        return jsonify({"error": "Debes enviar inicio y fin"}), 400

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d")

    # Agrupar por conductor
    resultados = (
        db.session.query(
            Conductor.nombre.label("conductor"),
            func.count(Despacho.id_despacho).label("total_servicios"),
            func.sum(Despacho.tarifa).label("total_tarifa")
        )
        .join(Despacho, Conductor.id_conductor == Despacho.conductor_id)
        .filter(Despacho.fecha_hora_inicio >= inicio_dt,
                Despacho.fecha_hora_inicio <= fin_dt)
        .group_by(Conductor.nombre)
        .all()
    )

    # Convertir a JSON
    data = [
        {
            "conductor": r.conductor,
            "total_servicios": r.total_servicios,
            "total_tarifa": float(r.total_tarifa) if r.total_tarifa else 0.0
        }
        for r in resultados
    ]

    return jsonify(data)