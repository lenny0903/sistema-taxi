from flask import Blueprint, request, jsonify
from extensions import db
from models.pago_cuotas import PagoCuota
from models.cuota_semanal import CuotaSemanal
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.conductores import Conductor
from app import MONTO_CUOTA_SEMANAL
pagos_bp = Blueprint('pagos', __name__)

@pagos_bp.route('/registrar', methods=['POST'])
@jwt_required()
def registrar_pago():
    data = request.json
    conductor_id = data.get('conductor_id')
    
    # Usamos su variable global
    MONTO_FIJO_VAL = 40000 
    
    id_usuario_jwt = get_jwt_identity()
    semana_actual = datetime.now().strftime('%Y-%U')

    try:
        # 1. Insertar en el historial (Asegúrese que PagoCuota también coincida con sus columnas)
        referencia_limpia = data.get('referencia', '').strip() or "EFECTIVO"

        # 2. Sincronizar el ESTADO DE LA SEMANA (Tabla cuotas_semanales)
        cuota = CuotaSemanal.query.filter_by(
            conductor_id=conductor_id, 
            semana_anio=semana_actual
        ).first()
        
        if cuota:
            cuota.pagado = True
            cuota.fecha_pago = datetime.now()
            cuota.monto_fijo = MONTO_FIJO_VAL # 👈 CAMBIADO: Antes decía monto_pagado
            cuota.referencia_pago = referencia_limpia # 👈 AGREGADO: Según su SQL
        else:
            # 🚀 Si no existe, la creamos con los nombres de su CREATE TABLE
            nueva_cuota = CuotaSemanal(
                conductor_id=conductor_id,
                semana_anio=semana_actual,
                monto_fijo=MONTO_FIJO_VAL, # 👈 CAMBIADO
                pagado=True,
                fecha_pago=datetime.now(),
                referencia_pago=referencia_limpia # 👈 CAMBIADO
            )
            db.session.add(nueva_cuota)
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Sincronizado con éxito"}), 201
        
    except Exception as e:
        db.session.rollback()
        # Este print es vital para ver el error real en la terminal de Linux
        print(f"❌ ERROR DE BASE DE DATOS: {str(e)}") 
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500
    
@pagos_bp.route('/recientes', methods=['GET'])
@jwt_required()
def obtener_pagos_recientes():
    # Consultamos los últimos 10 pagos haciendo un JOIN directo
    resultados = db.session.query(PagoCuota, Conductor.nombre)\
        .join(Conductor, PagoCuota.conductor_id == Conductor.id_conductor)\
        .order_by(PagoCuota.fecha_pago.desc()).limit(10).all()
    
    lista_pagos = [{
        "fecha_pago": p[0].fecha_pago.isoformat(),
        "conductor_nombre": p[1],
        "semana_anio": p[0].semana_anio,
        "monto_pagado": p[0].monto_pagado,
        "referencia": p[0].referencia
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
            esta_pagado = pagos_dict.get(c.id_conductor, False)

            # CALCULO DINÁMICO
            # 1. Lo que debería haber pagado hasta el sol de hoy
            deuda_acumulada = semana_actual_num * MONTO_CUOTA_SEMANAL
            
            # 2. Lo que ha pagado realmente (suma de cuotas marcadas como pagadas)
            total_abonado = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
                .filter(CuotaSemanal.conductor_id == c.id_conductor, 
                        CuotaSemanal.pagado == True).scalar() or 0.0
            
            saldo_real = deuda_acumulada - total_abonado
            

            resultado.append({
                "id_conductor": c.id_conductor,
                "unidad": c.codigo,
                "conductor": c.nombre,
                "saldo": f"{saldo_real:,.2f}", # 👈 AQUÍ ESTÁ EL CAMBIO CLAVE
                "pagado": esta_pagado,
                "status_html": (
                    '<span class="px-2 py-1 rounded bg-green-100 text-green-700 font-bold text-xs">PAGADO</span>' 
                    if esta_pagado else 
                    '<span class="px-2 py-1 rounded bg-red-100 text-red-700 font-bold text-xs">PENDIENTE</span>'
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