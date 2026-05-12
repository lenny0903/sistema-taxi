from flask import Blueprint, request, jsonify
from extensions import db
from models import conductores
from models.pago_cuotas import PagoCuota
from models.cuota_semanal import CuotaSemanal
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.conductores import Conductor
from app import MONTO_CUOTA_SEMANAL
from sqlalchemy import func, or_
pagos_bp = Blueprint('pagos', __name__)

from sqlalchemy import func # <--- IMPORTANTE: Agrega esto al inicio del archivo

@pagos_bp.route('/registrar', methods=['POST'])
@jwt_required()
def registrar_pago():
    data = request.json
    conductor_id = data.get('conductor_id')
    MONTO_FIJO_VAL = 40000.0 
    
    # NUEVO: Capturamos la novedad
    tipo_novedad = data.get('tipo_novedad', 'PAGO_NORMAL')
    es_exoneracion = tipo_novedad != 'PAGO_NORMAL'
    
    id_usuario_jwt = get_jwt_identity()
    ahora = datetime.now()
    semana_actual = ahora.strftime('%Y-%U')

    try:
        # Si es exoneración, forzamos la referencia con el motivo si viene vacío
        motivo_novedad = tipo_novedad.replace('_', ' ')
        referencia_limpia = data.get('referencia', '').strip()
        
        if es_exoneracion and not referencia_limpia:
            referencia_limpia = f"EXONERADO: {motivo_novedad}"
        elif not referencia_limpia:
            referencia_limpia = "EFECTIVO"

        metodo = data.get('metodo', 'Efectivo')
        if es_exoneracion:
            metodo = "EXONERACIÓN"

        # IMPORTANTE: El monto para el saldo sigue siendo 40k para nivelar, 
        # pero en reportes de caja (que usted hará luego) filtrará por 'metodo'
        monto_a_pagar = float(data.get('monto_pagado', MONTO_FIJO_VAL)) 

        # --- PASO 1: REGISTRAR EL ABONO (O EXONERACIÓN) ---
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
        db.session.flush() 

        # --- PASO 2: CALCULAR TOTAL (Aquí la magia sigue igual) ---
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
            cuota_control = CuotaSemanal(
                conductor_id=conductor_id,
                semana_anio=semana_actual,
                monto_fijo=MONTO_FIJO_VAL
            )
            db.session.add(cuota_control)
        
       # APLICAMOS LA LÓGICA DE SOLVENCIA E INCIDENCIAS
        if es_exoneracion:
            cuota_control.pagado = True  
            cuota_control.es_exonerado = True
            cuota_control.tipo_novedad = tipo_novedad
            cuota_control.referencia_pago = f"EXONERADO: {tipo_novedad.replace('_', ' ')}"
        else:
            # Si completó el pago en dinero
            if total_pagado >= MONTO_FIJO_VAL:
                cuota_control.pagado = True  
            else:
                cuota_control.pagado = False 
            
            cuota_control.es_exonerado = False
            cuota_control.tipo_novedad = 'PAGO_NORMAL'
            cuota_control.referencia_pago = referencia_limpia

        # Datos comunes para ambos casos
        cuota_control.fecha_pago = ahora

        db.session.commit()
        db.session.refresh(nuevo_pago) 

        from models.conductores import Conductor
        c = Conductor.query.get(conductor_id)

        return jsonify({
            "status": "success", 
            "id": nuevo_pago.id,
            "message": "✅ Registro exitoso",
            "monto": nuevo_pago.monto_pagado,
            "conductor": c.nombre,         
            "unidad": c.codigo,            
            "semana": nuevo_pago.semana_anio,
            "es_exoneracion": es_exoneracion # <--- Info extra para el JS
        }), 201
        
    except Exception as e:
        db.session.rollback()
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
        # Obtenemos solo los conductores que deben aparecer en el Dashboard
        conductores_aptos = Conductor.query.filter(
            Conductor.estado.in_(["disponible", "ocupado", "activo"])
        ).all()
        
        resultado = []
        semana_hoy = datetime.now().strftime('%Y-%U')

        for c in conductores_aptos:
            # --- INICIO DEL BLOQUE DE SEGURIDAD ---
            try:
                # 1. Buscamos cuota de la semana
                cuota_semanal = CuotaSemanal.query.filter_by(
                    conductor_id=c.id_conductor, 
                    semana_anio=semana_hoy
                ).first()

                # 2. Sumatorias (Aquí es donde SQLite explota con los strings vacíos '')
                total_cargos = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
                    .filter(CuotaSemanal.conductor_id == c.id_conductor).scalar() or 0.0
                
                total_abonos = db.session.query(db.func.sum(PagoCuota.monto_pagado))\
                    .filter(PagoCuota.conductor_id == c.id_conductor).scalar() or 0.0

                # 3. Cálculo de saldo
                saldo_real = total_cargos - total_abonos
                
                # Regla para nuevos
                if total_cargos == 0 and total_abonos == 0:
                    saldo_real = 40000.0 

                # 4. Solvencia
                esta_realmente_solvente = (saldo_real <= 0) or (cuota_semanal and cuota_semanal.pagado)

                if esta_realmente_solvente and saldo_real > 0:
                    saldo_real = 0.0

                # 5. Construcción del objeto JSON (Solo si no hubo error arriba)
                resultado.append({
                    "id_conductor": c.id_conductor,
                    "unidad": c.codigo,
                    "conductor": c.nombre,
                    "saldo": f"{max(0, saldo_real):,.2f}",
                    "pagado": esta_realmente_solvente,
                    "status_html": (
                        '<span class="px-2 py-1 rounded bg-green-100 text-green-700 font-bold text-xs">SOLVENTE</span>' 
                        if esta_realmente_solvente else 
                        '<span class="px-2 py-1 rounded bg-red-100 text-red-700 font-bold text-xs">DEUDOR</span>'
                    )
                })

            except Exception as e:
                # Si un conductor tiene basura en la DB, lo reportamos y SEGUIMOS
                print(f"⚠️ Error en datos de {c.nombre} (ID {c.id_conductor}): {str(e)}")
                continue 
            # --- FIN DEL BLOQUE DE SEGURIDAD ---

        # Ordenamiento: El que más debe primero
        def limpiar_saldo(x):
            try: return float(str(x['saldo']).replace(',', ''))
            except: return 0.0

        resultado.sort(key=limpiar_saldo, reverse=True)
        
        return jsonify(resultado), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error crítico en ruta /estado_semana: {str(e)}")
        return jsonify({"error": "Error interno al procesar la lista"}), 500
@pagos_bp.route('/inicializar_semana', methods=['POST'])
@jwt_required()
def inicializar_semana():
    # Usamos la variable global importada de app
    from app import MONTO_CUOTA_SEMANAL 
    
    # Generamos el identificador de la semana actual
    semana_control = datetime.now().strftime('%Y-%U') 

    try:
        # Solo conductores activos (disponibles)
        conductores = Conductor.query.filter(
            Conductor.estado.in_(["disponible", "ocupado", "activo"])
        ).all()
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
        monto_total = float(data.get('monto')) 
        referencia = data.get('referencia', 'NIVELACIÓN CUADERNO 2026')

        # 1. Recuperamos la identidad del usuario desde el JWT
        # Esto soluciona el error de usuario_id: None
        id_usuario_jwt = get_jwt_identity()

        # 2. Generamos la semana actual para el registro
        # Esto soluciona el error de semana_anio: None
        semana_actual = datetime.now().strftime('%Y-%U')

        conductor = Conductor.query.get_or_404(conductor_id)

        # 3. Construcción completa del objeto cumpliendo los NOT NULL
        nueva_nivelacion = PagoCuota(
            conductor_id=conductor_id,
            semana_anio=semana_actual,  # <--- CRÍTICO
            monto_pagado=monto_total,
            metodo_pago='Efectivo',     # Valor por defecto para nivelación
            referencia=referencia,
            usuario_id=id_usuario_jwt,   # <--- CRÍTICO para auditoría
            fecha_pago=datetime.now()
        )

        db.session.add(nueva_nivelacion)
        db.session.commit()

        return jsonify({
            "status": "success",
            "msg": f"Nivelación exitosa para Unidad {conductor.codigo}", # Use .codigo si es el de la unidad
            "monto_cargado": monto_total
        }), 200

    except Exception as e:
        db.session.rollback()
        # El print le dirá exactamente qué campo falta si persiste el error
        print(f"❌ Error en nivelación: {str(e)}") 
        return jsonify({"error": f"Error de integridad: {str(e)}"}), 500