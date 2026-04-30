from flask import Blueprint, request, jsonify
from extensions import db
from models import conductores
from models.pago_cuotas import PagoCuota
from models.cuota_semanal import CuotaSemanal
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.conductores import Conductor
from app import MONTO_CUOTA_SEMANAL
pagos_bp = Blueprint('pagos', __name__)

from sqlalchemy import func # <--- IMPORTANTE: Agrega esto al inicio del archivo

@pagos_bp.route('/registrar', methods=['POST'])
@jwt_required()
def registrar_pago():
    data = request.json
    conductor_id = data.get('conductor_id')
    MONTO_FIJO_VAL = 40000.0 
    
    id_usuario_jwt = get_jwt_identity()
    ahora = datetime.now()
    semana_actual = ahora.strftime('%Y-%U')

    try:
        referencia_limpia = data.get('referencia', '').strip() or "EFECTIVO"
        metodo = data.get('metodo', 'Efectivo')
        monto_a_pagar = float(data.get('monto', MONTO_FIJO_VAL)) # Recibimos el monto del form

        # --- PASO 1: REGISTRAR EL ABONO EN EL HISTORIAL ---
        nuevo_pago = PagoCuota(
            conductor_id=conductor_id,
            semana_anio=semana_actual,
            monto_pagado=monto_a_pagar,
            metodo_pago=metodo,
            referencia=referencia_limpia,
            usuario_id=id_usuario_jwt,
            fecha_pago=ahora
        )
        db.session.add(nuevo_pago)
        
        # Guardamos temporalmente para que la suma incluya este nuevo pago
        db.session.flush() 

        # --- PASO 2: CALCULAR TOTAL PAGADO EN LA SEMANA ---
        total_pagado = db.session.query(func.sum(PagoCuota.monto_pagado)).filter(
            PagoCuota.conductor_id == conductor_id,
            PagoCuota.semana_anio == semana_actual
        ).scalar() or 0

        # --- PASO 3: ACTUALIZAR EL ESTADO DE SOLVENCIA ---
        cuota_control = CuotaSemanal.query.filter_by(
            conductor_id=conductor_id, 
            semana_anio=semana_actual
        ).first()

        if not cuota_control:
            # Si no existe el registro de la semana, lo creamos
            cuota_control = CuotaSemanal(
                conductor_id=conductor_id,
                semana_anio=semana_actual,
                monto_fijo=MONTO_FIJO_VAL
            )
            db.session.add(cuota_control)

        # La lógica que mencionaste:
        if total_pagado >= MONTO_FIJO_VAL:
            cuota_control.pagado = True  # ¡SOLVENTE!
        else:
            cuota_control.pagado = False # PENDIENTE (Abono parcial)
        
        cuota_control.fecha_pago = ahora
        cuota_control.referencia_pago = referencia_limpia

       # --- PASO 4: COMMIT Y REFRESH ---
        db.session.add(nuevo_pago)
        db.session.commit()
        db.session.refresh(nuevo_pago) 

        from models.conductores import Conductor
        c = Conductor.query.get(conductor_id)

        return jsonify({
            "status": "success", 
            "id": nuevo_pago.id,  # <--- Esta es la llave que busca el JS
            "message": f"✅ Registrado con Control Interno: {nuevo_pago.id:05d}",
            "monto": nuevo_pago.monto_pagado,
            "conductor": c.nombre,         
            "unidad": c.codigo,            
            "semana": nuevo_pago.semana_anio,
            "fecha": ahora.strftime('%d/%m/%Y, %I:%M %p'),
            "ref": nuevo_pago.referencia       
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}") 
        return jsonify({"status": "error", "message": str(e)}), 500
    
@pagos_bp.route('/recientes', methods=['GET'])
@jwt_required()
def obtener_pagos_recientes():
    resultados = db.session.query(PagoCuota, Conductor.nombre)\
        .join(Conductor, PagoCuota.conductor_id == Conductor.id_conductor)\
        .order_by(PagoCuota.fecha_pago.desc()).limit(10).all()
    
    lista_pagos = [{
        "fecha": p[0].fecha_pago.strftime('%d/%m/%Y, %I:%M %p'),
        "conductor": p[1],
        "semana": p[0].semana_anio,
        "monto": p[0].monto_pagado,
        "ref": p[0].referencia # <--- Asegúrese que sea 'ref'
    } for p in resultados]
    
    return jsonify(lista_pagos)

@pagos_bp.route('/estado_semana', methods=['GET'])
@jwt_required()
def obtener_estado_semana():
    try:
        hoy = datetime.now()
        semana_actual_str = hoy.strftime('%Y-%U')
        # Obtenemos el número de semana actual (ej. 17) para saber cuánto debería haber pagado
        semana_actual_num = int(hoy.strftime('%U')) 

        conductores_aptos = Conductor.query.filter_by(estado="disponible").all()
        
        pagos_semanales = CuotaSemanal.query.filter_by(semana_anio=semana_actual_str).all()
        pagos_dict = {p.conductor_id: p.pagado for p in pagos_semanales}

        resultado = []
        hoy = datetime.now()
        semana_actual_num = int(hoy.strftime('%U')) # Semana del año (0-52)

        for c in conductores_aptos:
            # 1. Calculamos la deuda total acumulada a la fecha
            deuda_total_acumulada = semana_actual_num * MONTO_CUOTA_SEMANAL
            
            # 2. Sumamos TODOS sus pagos históricos (incluyendo cargas iniciales)
            total_pagado_historico = db.session.query(db.func.sum(PagoCuota.monto_pagado))\
                .filter(PagoCuota.conductor_id == c.id_conductor).scalar() or 0.0
            
            # Agregamos también lo que venga de CuotaSemanal si hubo carga inicial allí
            total_historico_cuotas = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
                .filter(CuotaSemanal.conductor_id == c.id_conductor, 
                        CuotaSemanal.semana_anio == "HISTORICO-2026").scalar() or 0.0

            saldo_real = deuda_total_acumulada - (total_pagado_historico + total_historico_cuotas)
            
            # EL CAMBIO CLAVE: Solvente solo si el saldo es 0 o menor
            esta_realmente_solvente = saldo_real <= 0

            resultado.append({
                "id_conductor": c.id_conductor,
                "unidad": c.codigo,
                "conductor": c.nombre,
                "saldo": f"{saldo_real:,.2f}",
                "pagado": esta_realmente_solvente,
                "status_html": (
                    '<span class="px-2 py-1 rounded bg-green-100 text-green-700 font-bold text-xs">SOLVENTE</span>' 
                    if esta_realmente_solvente else 
                    '<span class="px-2 py-1 rounded bg-red-100 text-red-700 font-bold text-xs">DEUDOR</span>'
                )
            })

        # Ordenar: primero los pendientes, luego los pagados
        resultado.sort(key=lambda x: x['pagado'])
        return jsonify(resultado), 200

    except Exception as e:
        print(f"❌ Error en estado_semana: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@pagos_bp.route('/inicializar_semana', methods=['POST'])
@jwt_required()
def inicializar_semana():
    semana_control = datetime.now().strftime('%Y-%U') 

    # Cambiado a 'disponible' para ser coherente con la tabla de arriba
    conductores = Conductor.query.filter_by(estado="disponible").all()
    conteo = 0

    for c in conductores:
        existe = CuotaSemanal.query.filter_by(
            conductor_id=c.id_conductor, 
            semana_anio=semana_control
        ).first()

        if not existe:
            nueva_cuota = CuotaSemanal(
                conductor_id=c.id_conductor,
                semana_anio=semana_control,
                monto_fijo=40000.0, # Use su variable global aquí
                pagado=False 
            )
            db.session.add(nueva_cuota)
            conteo += 1
    
    db.session.commit()
    return jsonify({"message": f"Se inicializaron {conteo} conductores para la semana {semana_control}."})

# Dentro de registrar_pagos.py

@pagos_bp.route('/carga_inicial_pagos', methods=['POST'])
@jwt_required()
def carga_inicial_pagos():
    try:
        data = request.get_json()
        conductor_id = data.get('conductor_id')
        monto_total = float(data.get('monto')) # Lo que ella escriba en el modal
        referencia = data.get('referencia', 'CARGA INICIAL SISTEMA')

        # Buscamos al conductor
        conductor = Conductor.query.get_or_404(conductor_id)

        # Creamos un registro especial de abono masivo
        nuevo_pago = CuotaSemanal(
            conductor_id=conductor_id,
            monto_fijo=monto_total, # Aquí guardamos el total de la nivelación
            semana_anio="HISTORICO-2026", # Una etiqueta para saber que es carga inicial
            pagado=True,
            referencia_pago=referencia,
            fecha_pago=datetime.now()
        )

        db.session.add(nuevo_pago)
        db.session.commit()

        return jsonify({"msg": "Carga inicial procesada con éxito", "nuevo_saldo": "calculado"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500