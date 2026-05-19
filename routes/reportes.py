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
    
@reporte_bp.route('/consolidado_pagos', methods=['GET'])
def reporte_consolidado_pagos():
    try:
        # 1. Traer todos los conductores para cruzarlos
        conductores = Conductor.query.order_by(Conductor.codigo).all()
        
        resultado_conductores = []
        gran_total_dinero = 0.0
        gran_total_semanas = 0

        # 2. Procesar conductor por conductor
        for c in conductores:
            # Sumamos solo el dinero real pagado por este conductor
            total_dinero_conductor = db.session.query(db.func.sum(CuotaSemanal.monto_fijo)) \
                .filter(
                    CuotaSemanal.conductor_id == c.id_conductor,
                    CuotaSemanal.pagado == True,
                    CuotaSemanal.es_exonerado == False  # 🎯 Dinero real
                ).scalar() or 0.0

            # Contamos TODAS las semanas cubiertas (Pagos + Exoneraciones)
            total_semanas_conductor = CuotaSemanal.query.filter(
                CuotaSemanal.conductor_id == c.id_conductor,
                CuotaSemanal.pagado == True  # 🎯 Ya liberadas
            ).count()

            # Acumulamos para el Gran Total del reporte
            gran_total_dinero += float(total_dinero_conductor)
            gran_total_semanas += total_semanas_conductor

            # Añadimos la fila del conductor si tiene movimientos (o lo muestra en cero si prefiere)
            resultado_conductores.append({
                "unidad": c.codigo,
                "conductor": c.nombre,
                "total_pagado_raw": float(total_dinero_conductor), # Para lógicas del JS si hiciera falta
                "total_pagado": f"{total_dinero_conductor:,.2f}",
                "semanas_cubiertas": total_semanas_conductor
            })

        # 3. Retornamos la data de los choferes Y los Totales Generales separados
        return jsonify({
            "status": "success",
            "totales_generales": {
                "gran_total_dinero": f"{gran_total_dinero:,.2f}",
                "gran_total_semanas": gran_total_semanas
            },
            "data": resultado_conductores
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500    
    


@reporte_bp.route('/pdf_consolidado', methods=['GET'])
def exportar_pdf_consolidado():
    try:
        # IMPORTACIONES LOCALES ABSOLUTAMENTE SEGURAS
        from app import db
        import io
        from models import Conductor, CuotaSemanal
        from datetime import datetime
        
        # 🎯 CONTROL DE IMPORTACIONES CON LAS RUTAS REALES DE REPORTLAB
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        # 1. Obtener los datos frescos de la Base de Datos
        conductores = Conductor.query.order_by(Conductor.codigo).all()
        gran_total_dinero = 0.0
        gran_total_semanas = 0
        
        # Estilos de texto para las celdas
        style_header = ParagraphStyle('H_Tab', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=1)
        style_header_left = ParagraphStyle('H_TabL', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=0)
        style_header_right = ParagraphStyle('H_TabR', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=2)
        
        style_cell = ParagraphStyle('Cell', fontName='Helvetica', fontSize=8.5, leading=11)
        style_cell_center = ParagraphStyle('CellC', fontName='Helvetica', fontSize=8.5, alignment=1)
        style_cell_right = ParagraphStyle('CellR', fontName='Helvetica-Bold', fontSize=8.5, alignment=2)
        style_cell_nota = ParagraphStyle('CellN', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.HexColor('#64748b'))

        # Cabecera física de la tabla
        tabla_datos = [[
            Paragraph('<b>Unidad</b>', style_header),
            Paragraph('<b>Conductor</b>', style_header_left),
            Paragraph('<b>Total Pagado (COP)</b>', style_header_right),
            Paragraph('<b>Semanas</b>', style_header),
            Paragraph('<b>Observaciones de Auditoría</b>', style_header_left)
        ]]

        for c in conductores:
            total_dinero = db.session.query(db.func.sum(CuotaSemanal.monto_fijo)) \
                .filter(
                    CuotaSemanal.conductor_id == c.id_conductor,
                    CuotaSemanal.pagado == True,
                    CuotaSemanal.es_exonerado == False
                ).scalar() or 0.0

            total_semanas = CuotaSemanal.query.filter(
                CuotaSemanal.conductor_id == c.id_conductor,
                CuotaSemanal.pagado == True
            ).count()

            gran_total_dinero += float(total_dinero)
            gran_total_semanas += total_semanas

            nota = "Sin movimientos"
            if total_semanas > 0:
                if total_dinero == 0:
                    nota = f"{total_semanas} sem. exoneradas (Auditoría Limpia)"
                else:
                    nota = "Solvente en taquilla / Nivelaciones"

            monto_formateado = f"${total_dinero:,.2f}" if total_dinero > 0 else "$0.00"

            # Inyectamos strings planos procesados por Python, cero Jinja2
            tabla_datos.append([
                Paragraph(f"<b>{c.codigo}</b>", style_cell_center),
                Paragraph(c.nombre or "Conductor sin nombre", style_cell),
                Paragraph(monto_formateado, style_cell_right),
                Paragraph(f"{total_semanas} sem", style_cell_center),
                Paragraph(nota, style_cell_nota)
            ])

        # Formateamos los grandes totales con Python puro antes de pasarlos a ReportLab
        gran_total_formateado = f"${gran_total_dinero:,.2f}"
        
        # Fila del Gran Total con colspan manual configurado en el TableStyle
        tabla_datos.append([
            Paragraph('<b>TOTAL CONSOLIDADO:</b>', ParagraphStyle('TotalL', fontName='Helvetica-Bold', fontSize=9, alignment=2)),
            '', # Celda vacía requerida por el SPAN
            Paragraph(gran_total_formateado, ParagraphStyle('TotalM', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#15803d'), alignment=2)),
            Paragraph(f"{gran_total_semanas} sem", ParagraphStyle('TotalS', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#1d4ed8'), alignment=1)),
            Paragraph('Consolidación de caja limpia y condonaciones.', style_cell_nota)
        ])

        # 2. Configurar el documento en memoria RAM
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=1.5*cm, bottomMargin=1.5*cm
        )
        
        story = []

        # Títulos e Identificación del Reporte
        story.append(Paragraph("REPORTE CONSOLIDADO DE AUDITORÍA", ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=18, leading=22, spaceAfter=4)))
        story.append(Paragraph("Control de Semanas vs. Montos Recaudados — Cooperativa SIM", ParagraphStyle('Sub', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#4f46e5'), spaceAfter=12)))
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        meta_text = f"<b>Fecha Emisión:</b> {fecha_actual} | <b>Filtro:</b> Año Fiscal 2026 | <b>Estado:</b> Cierre de Ciclo"
        story.append(Paragraph(meta_text, ParagraphStyle('Meta', fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#718096'), spaceAfter=15)))

        # 3. Construir la Tabla Física con anchos medidos para A4 (~17.4 cm totales)
        col_widths = [1.8*cm, 5.2*cm, 3.2*cm, 2.2*cm, 5.0*cm]
        t = Table(tabla_datos, colWidths=col_widths, repeatRows=1)
        
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')), # Cabecera oscura
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')), # Rejillas internas
            ('SPAN', (0, -1), (1, -1)), # Une la celda 0 y 1 de la última fila (TOTAL CONSOLIDADO)
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')), # Fila de totales
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#94a3b8')),
        ]
        
        # Alternar colores en las filas de datos para legibilidad (Cebrado)
        for i in range(1, len(tabla_datos) - 1):
            if i % 2 == 0:
                t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
                
        t.setStyle(TableStyle(t_style))
        story.append(t)

        # Renderizar estructura al buffer binario
        doc.build(story)
        buffer.seek(0)

        # 4. Enviar el flujo binario como un archivo de descarga directa
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"Reporte_Consolidado_Auditoria_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        # Si algo falla, este print saldrá directo en tu terminal activa para verlo
        print(f"❌ [ERROR CRÍTICO PDF]: {str(e)}")
        return jsonify({"status": "error", "message": f"Error en ReportLab: {str(e)}"}), 500