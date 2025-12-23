from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import Despacho, Conductor
from app import db
from sqlalchemy import func
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file

reporte_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

# -------------------------------
# 📌 Reporte por conductor (sin rango de fechas)
# -------------------------------
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

# -------------------------------
# 📌 Reporte general entre fechas
# -------------------------------
@reporte_bp.route("/", methods=["GET"])
def reportes():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not inicio or not fin:
        return jsonify({"error": "Debes enviar inicio y fin"}), 400

    # Convertir a datetime y extender fin hasta el final del día
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    # 🔎 Filtrar solo por fecha de fin y estado finalizado
    despachos = (
        db.session.query(Despacho)
        .filter(
            Despacho.fecha_hora_fin >= inicio_dt,
            Despacho.fecha_hora_fin <= fin_dt,
            Despacho.estado_despacho == "finalizado"
        )
        .all()
    )

    resultado = [
        {
            "id_despacho": d.id_despacho,
            "cliente_nombre": d.cliente.nombre if d.cliente else "-",
            "conductor_codigo": d.conductor.codigo if d.conductor else "-",
            "conductor_nombre": d.conductor.nombre if d.conductor else "-",
            "auto_placa": d.auto.nro_placa if d.auto else "-",
            "origen": d.origen_despacho or "-",
            "destino": d.destino_despacho or "-",
            "fecha": d.fecha_hora_fin.strftime("%Y-%m-%d %H:%M") if d.fecha_hora_fin else "-",
            "tarifa": d.tarifa or 0.0
        }
        for d in despachos
    ]

    return jsonify(resultado)


# -------------------------------
# 📌 Reporte agregado por conductor entre fechas
# -------------------------------
@reporte_bp.route("/conductores", methods=["GET"])
def reportes_conductores():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not inicio or not fin:
        return jsonify({"error": "Debes enviar inicio y fin"}), 400

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    resultados = (
        db.session.query(
            Conductor.nombre.label("conductor"),
            func.count(Despacho.id_despacho).label("total_servicios"),
            func.sum(Despacho.tarifa).label("total_tarifa")
        )
        .join(Despacho, Conductor.id_conductor == Despacho.conductor_id)
        .filter(
            Despacho.fecha_hora_fin >= inicio_dt,
            Despacho.fecha_hora_fin <= fin_dt,
            Despacho.estado_despacho == "finalizado"   # 👈 solo viajes cerrados
        )
        .group_by(Conductor.nombre)
        .all()
    )

    data = [
        {
            "conductor": r.conductor,
            "total_servicios": r.total_servicios,
            "total_tarifa": float(r.total_tarifa) if r.total_tarifa else 0.0
        }
        for r in resultados
    ]

    return jsonify(data)

@reporte_bp.route("/pdf", methods=["GET"])
def reporte_pdf():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    despachos = (
        db.session.query(Despacho)
        .filter(
            Despacho.fecha_hora_fin >= inicio_dt,
            Despacho.fecha_hora_fin <= fin_dt,
            Despacho.estado_despacho == "finalizado"
        )
        .all()
    )

    filename = "reporte.pdf"
    c = canvas.Canvas(filename, pagesize=letter)

    # 🔹 Encabezados de tabla
    y = 750
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Código")
    c.drawString(100, y, "Conductor")
    c.drawString(250, y, "Placa")
    c.drawString(320, y, "Cliente")
    c.drawString(450, y, "Tarifa")
    y -= 20

    # 🔹 Filas de datos
    c.setFont("Helvetica", 9)
    for d in despachos:
        c.drawString(50, y, str(d.conductor.codigo))
        c.drawString(100, y, d.conductor.nombre)
        c.drawString(250, y, d.auto.nro_placa)
        c.drawString(320, y, d.cliente.nombre)
        c.drawString(450, y, str(d.tarifa))
        y -= 20

        if y < 50:  # salto de página
            c.showPage()
            y = 750
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "Código")
            c.drawString(100, y, "Conductor")
            c.drawString(250, y, "Placa")
            c.drawString(320, y, "Cliente")
            c.drawString(450, y, "Tarifa")
            y -= 20
            c.setFont("Helvetica", 9)

    c.save()
    return send_file(filename, as_attachment=True)


@reporte_bp.route("/embarque_desembarque", methods=["GET"])
def reporte_embarque_desembarque():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not inicio or not fin:
        return jsonify({"error": "Debes enviar inicio y fin"}), 400

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

    despachos = (
        db.session.query(Despacho)
        .filter(
            Despacho.fecha_hora_fin >= inicio_dt,
            Despacho.fecha_hora_fin <= fin_dt,
            Despacho.estado_despacho == "finalizado",
            Despacho.fecha_hora_embarque.isnot(None),   # 🚨 blindaje
            Despacho.fecha_hora_fin.isnot(None)         # 🚨 blindaje
        )
        .all()
    )

    resultado = [
        {
            "nro": idx + 1,
            "cliente": d.cliente.nombre if d.cliente else "-",
            "telefono_cliente": d.cliente.telefono if d.cliente else "-",
            "conductor_codigo": d.conductor.codigo if d.conductor else "-",
            "conductor_nombre": d.conductor.nombre if d.conductor else "-",
            "auto_placa": d.auto.nro_placa if d.auto else "-",
            "origen": d.origen_despacho or "-",
            "embarque": d.fecha_hora_embarque.strftime("%H:%M") if d.fecha_hora_embarque else "-",
            "destino": d.destino_despacho or "-",
            "desembarque": d.fecha_hora_fin.strftime("%H:%M") if d.fecha_hora_fin else "-"
        }
        for idx, d in enumerate(despachos)
    ]

    return jsonify({
        "fecha_reporte": datetime.now().strftime("%Y-%m-%d"),
        "rango": f"Del {inicio} al {fin}",
        "data": resultado
    })



