from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from extensions import db
from models import Despacho, Conductor, Usuario, Auto
from models.clientes import Cliente
from models.cuota_semanal import CuotaSemanal
from models.pago_cuotas import PagoCuota

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
reporte_bp = Blueprint('reportes', __name__)

@reporte_bp.route("/conductores", methods=["GET"])
def reportes_por_conductor():
    try:
        inicio = request.args.get("inicio")
        fin = request.args.get("fin")

        if not inicio or not fin:
            return jsonify({"error": "Debes enviar inicio y fin"}), 400

        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
        fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

        resultados = (
            db.session.query(
                Conductor.nombre.label("nombre_conductor"),
                func.count(Despacho.id_despacho).label("total_servicios"),
                func.sum(Despacho.tarifa).label("total_tarifa")
            )
            .join(Despacho, Conductor.id_conductor == Despacho.conductor_id)
            .filter(
                Despacho.fecha_hora_fin >= inicio_dt,
                Despacho.fecha_hora_fin <= fin_dt,
                Despacho.estado_despacho == "finalizado"
            )
            .group_by(Conductor.nombre)
            .all()
        )

        data = [
            {
                "conductor": r.nombre_conductor,   # 👈 usar alias correcto
                "total_servicios": r.total_servicios,
                "total_tarifa": float(r.total_tarifa) if r.total_tarifa else 0.0
            }
            for r in resultados
        ]

        return jsonify(data)

    except Exception as e:
        current_app.logger.error(f"Error en /reportes/conductores: {e}")
        return jsonify({"error": "Error interno al generar reporte por conductor"}), 500


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
           
            "cliente_telefono": d.cliente.telefono if d.cliente else "-", 
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
            Conductor.nombre.label("nombre_conductor"),
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
            #"origen": d.origen_despacho or "-",
           "embarque": d.fecha_hora_inicio.strftime("%H:%M") if d.fecha_hora_inicio else "-",
            #"destino": d.destino_despacho or "-",
            "desembarque": d.fecha_hora_fin.strftime("%H:%M") if d.fecha_hora_fin else "-"
        }
        for idx, d in enumerate(despachos)
    ]

    return jsonify({
        "fecha_reporte": datetime.now().strftime("%Y-%m-%d"),
        "rango": f"Del {inicio} al {fin}",
        "data": resultado
    })


# -------------------------------
# 📌 Reporte por cliente (conductores que lo atendieron)
# -------------------------------
@reporte_bp.route("/cliente", methods=["GET"])
@jwt_required()
def reporte_por_cliente():
    telefono = request.args.get("telefono")
    if not telefono:
        return jsonify({"error": "Debes enviar el número de teléfono"}), 400

    try:
        resultados = (
            db.session.query(
                Conductor.codigo,
                Conductor.nombre,
                Despacho.origen_despacho,
                Despacho.destino_despacho,
                Despacho.fecha_hora_fin
            )
            .join(Conductor, Conductor.id_conductor == Despacho.conductor_id)
            .join(Cliente, Cliente.id_cliente == Despacho.cliente_id)
            .filter(
                Cliente.telefono == telefono,
                Despacho.estado_despacho == "finalizado"
            )
            .all()
        )

        data = []
        for r in resultados:
            ultima = r.fecha_hora_fin.strftime("%Y-%m-%d %H:%M") if r.fecha_hora_fin else "-"
            data.append({
                "nombre_conductor": f"{r.codigo} - {r.nombre}",  # 👈 código+nombre
                "origen": r.origen_despacho,
                "destino": r.destino_despacho,
                "ultima_fecha": ultima
            })

        print("➡️ Data enviada al frontend:", data)
        return jsonify(data)

    except Exception as e:
        print("❌ Error en reporte_por_cliente:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------
# 📌 Reporte de Pagos (Cierre de Caja)
# -------------------------------
# Asegúrese de agregar current_app a sus imports de flask


@reporte_bp.route("/pagos", methods=["GET"])
@jwt_required()
def reporte_pagos_contabilidad():
    try:
        inicio = request.args.get("inicio")
        fin = request.args.get("fin")

        if not inicio or not fin:
            return jsonify({"error": "Faltan fechas"}), 400

        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
        fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

        # 🔎 REVISIÓN: Usamos CuotaSemanal (NO PagoCuota)
        resultados = db.session.query(
            CuotaSemanal, 
            Conductor
        ).join(Conductor, CuotaSemanal.conductor_id == Conductor.id_conductor)\
         .filter(
            CuotaSemanal.pagado == True,
            CuotaSemanal.fecha_pago >= inicio_dt,
            CuotaSemanal.fecha_pago <= fin_dt
        ).all()

        lista_pagos = []
        total_acumulado = 0.0

        for cuota, conductor in resultados:
            # Usamos monto_fijo que es el nombre en su modelo
            monto = float(cuota.monto_fijo) if cuota.monto_fijo else 0.0
            total_acumulado += monto
            
            lista_pagos.append({
                "fecha_pago": cuota.fecha_pago.strftime("%Y-%m-%d %H:%M") if cuota.fecha_pago else "-",
                "conductor": f"{conductor.codigo} - {conductor.nombre}",
                "numero_unidad": getattr(conductor, 'id_unidad', '-'), 
                "monto": monto,
                "metodo_pago": "Registrado", 
                "referencia": cuota.referencia_pago or "-"
            })

        return jsonify({
            "pagos": lista_pagos,
            "totales": {
                "efectivo": total_acumulado,
                "transferencia": 0.0,
                "total_general": total_acumulado
            }
        })

    except Exception as e:
        # Ahora current_app funcionará porque lo importamos arriba
        current_app.logger.error(f"❌ Error en contabilidad: {str(e)}")
        # También lo imprimimos en la consola para verlo rápido
        print(f"❌ ERROR EN REPORTE PAGOS: {str(e)}")
        return jsonify({"error": "Error interno al procesar pagos"}), 500
    

@reporte_bp.route("/generar_cierre_pdf", methods=["GET"]) # <-- CAMBIAMOS NOMBRE PARA EVITAR CACHE
#@jwt_required()
def funcion_pdf_cierre_caja():
    try:
        # 🛡️ VALIDACIÓN MANUAL (Seguridad de "Los Patriotas")
        token_url = request.args.get("token")
        if not token_url or token_url == "null":
            return "Acceso denegado: Token faltante", 401
            
        try:
            from flask_jwt_extended import decode_token
            decode_token(token_url) # Esto valida que el token sea real y vigente
        except:
            return "Sesión inválida o expirada", 401
        inicio = request.args.get("inicio")
        fin = request.args.get("fin")
        
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
        fin_dt = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

        resultados = db.session.query(CuotaSemanal, Conductor).join(
            Conductor, CuotaSemanal.conductor_id == Conductor.id_conductor
        ).filter(
            CuotaSemanal.pagado == True,
            CuotaSemanal.fecha_pago >= inicio_dt,
            CuotaSemanal.fecha_pago <= fin_dt
        ).all()

        filepath = f"/tmp/cierre_{inicio}.pdf"
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("CIERRE DE CAJA - LOS PATRIOTAS", styles['Title']))
        elements.append(Paragraph(f"Período: {inicio} al {fin}", styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [["Fecha", "Conductor", "Referencia", "Monto (COP)"]]
        total = 0
        for cuota, cond in resultados:
            monto = float(cuota.monto_fijo or 0)
            total += monto
            data.append([
                cuota.fecha_pago.strftime("%d/%m %H:%M"),
                f"{cond.codigo} - {cond.nombre}",
                cuota.referencia_pago or "-",
                f"{monto:,.0f}"
            ])
        
        data.append(["", "", "TOTAL GENERAL:", f"{total:,.0f} COP"])

        t = Table(data, colWidths=[80, 200, 100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        elements.append(t)
        doc.build(elements)

        return send_file(filepath, as_attachment=True, download_name=f"Cierre_{inicio}.pdf")
    except Exception as e:
        print(f"❌ ERROR PDF: {e}")
        return jsonify({"error": str(e)}), 500