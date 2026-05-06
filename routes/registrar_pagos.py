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
        conductores_aptos = Conductor.query.filter_by(estado="disponible").all()
        resultado = []

        for c in conductores_aptos:
            # 1. CARGOS: Solo sumamos lo que la administradora cargó en la tabla
            # (Aquí entrarán los 40k semanales y las Cargas Iniciales de deuda vieja)
            total_cargos = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
                .filter(CuotaSemanal.conductor_id == c.id_conductor).scalar() or 0.0
            
            # 2. ABONOS: Sumamos todos los pagos reales
            total_abonos = db.session.query(db.func.sum(PagoCuota.monto_pagado))\
                .filter(PagoCuota.conductor_id == c.id_conductor).scalar() or 0.0

            # 3. SALDO: Diferencia real
            saldo_real = total_cargos - total_abonos
            
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

        # Ordenar por el que más debe
        resultado.sort(key=lambda x: float(x['saldo'].replace(',', '')), reverse=True)
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"❌ Error en estado_semana: {str(e)}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"❌ Error en estado_semana: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@pagos_bp.route('/inicializar_semana', methods=['POST'])
@jwt_required()
def inicializar_semana():
    # Usamos la variable global importada de app
    from app import MONTO_CUOTA_SEMANAL 
    
    # Generamos el identificador de la semana actual
    semana_control = datetime.now().strftime('%Y-%U') 

    try:
        # Solo conductores activos (disponibles)
        conductores = Conductor.query.filter_by(estado="disponible").all()
        conteo = 0

        for c in conductores:
            # VALIDACIÓN CRÍTICA: Evita cargar dos veces la misma semana si dan doble clic
            existe = CuotaSemanal.query.filter_by(
                conductor_id=c.id_conductor, 
                semana_anio=semana_control
            ).first()

            if not existe:
                nueva_cuota = CuotaSemanal(
                    conductor_id=c.id_conductor,
                    semana_anio=semana_control,
                    monto_fijo=MONTO_CUOTA_SEMANAL, # Usamos la global
                    pagado=False 
                )
                db.session.add(nueva_cuota)
                conteo += 1
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"✅ Se cargó la semana {semana_control} a {conteo} conductores.",
            "semana": semana_control,
            "monto_aplicado": MONTO_CUOTA_SEMANAL
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al inicializar semana: {str(e)}")
        return jsonify({"status": "error", "message": "No se pudo inicializar la semana."}), 500
# Dentro de registrar_pagos.py

@pagos_bp.route('/carga_inicial_pagos', methods=['POST'])
@jwt_required()
def carga_inicial_pagos():
    try:
        data = request.get_json()
        conductor_id = data.get('conductor_id')
        # Es el monto total que la administradora leyó en el cuaderno
        monto_total = float(data.get('monto')) 
        referencia = data.get('referencia', 'NIVELACIÓN CUADERNO 2026')

        # Buscamos al conductor para validar que existe
        conductor = Conductor.query.get_or_404(conductor_id)

        # REGISTRO CONTABLE: Usamos PagoCuota para que reste del saldo
        # Esto genera un saldo negativo (a favor) si no hay cargos previos
        nueva_nivelacion = PagoCuota(
            conductor_id=conductor_id,
            monto_pagado=monto_total,
            referencia=referencia,
            fecha_pago=datetime.now()
        )

        db.session.add(nueva_nivelacion)
        db.session.commit()

        # Retornamos éxito para que el JS refresque la tabla
        return jsonify({
            "status": "success",
            "msg": f"Nivelación exitosa para Unidad {conductor.unidad}",
            "monto_cargado": monto_total
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en nivelación: {str(e)}")
        return jsonify({"error": "No se pudo procesar la nivelación"}), 500