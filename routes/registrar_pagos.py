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

        
        
        # --- PASO 3: LÓGICA DE SOLVENCIA (CASCADA O EXONERACIÓN) ---
        
        if es_exoneracion:
            # Si es exoneración, actuamos sobre la semana actual específicamente
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
            
            cuota_control.pagado = True  
            cuota_control.es_exonerado = True
            cuota_control.tipo_novedad = tipo_novedad
            cuota_control.referencia_pago = f"EXONERADO: {tipo_novedad.replace('_', ' ')}"
            cuota_control.fecha_pago = ahora
        
        else:
            # SI ES PAGO NORMAL -> ACTIVAMOS LA CASCADA 🌊
            monto_restante = monto_a_pagar
            
            # Buscamos deudas viejas (pagado=False)
            cuotas_pendientes = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id, 
                pagado=False
            ).order_by(CuotaSemanal.semana_anio.asc()).all()

            for cuota in cuotas_pendientes:
                if monto_restante <= 0:
                    break
                
                falta_por_pagar = cuota.monto_fijo
                
                if monto_restante >= falta_por_pagar:
                    cuota.pagado = True
                    cuota.fecha_pago = ahora
                    cuota.referencia_pago = referencia_limpia
                    cuota.tipo_novedad = 'PAGO_NORMAL'
                    monto_restante -= falta_por_pagar
                else:
                    # Pago parcial: no marcamos como 'pagado' pero el saldo global bajará
                    break

            # Verificamos si existe la semana actual, si no, la creamos
            cuota_hoy = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id, 
                semana_anio=semana_actual
            ).first()

            if not cuota_hoy:
                nueva_cuota = CuotaSemanal(
                    conductor_id=conductor_id,
                    semana_anio=semana_actual,
                    monto_fijo=MONTO_FIJO_VAL,
                    pagado=(monto_restante >= MONTO_FIJO_VAL),
                    tipo_novedad='PAGO_NORMAL',
                    referencia_pago=referencia_limpia if monto_restante >= MONTO_FIJO_VAL else '',
                    fecha_pago=ahora if monto_restante >= MONTO_FIJO_VAL else None
                )
                db.session.add(nueva_cuota)

        # FINALIZAMOS TRANSACCIÓN
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
        # Importamos el monto global
        from app import MONTO_CUOTA_SEMANAL
        
        # --- BLOQUE DE AUTONOMÍA: EL "RELOJ" DEL VIERNES ---
        ahora = datetime.now()
        dia_semana = ahora.weekday() # 0=Lunes... 4=Viernes
        semana_hoy = ahora.strftime('%Y-%U')

        conductores_aptos = Conductor.query.filter(
            Conductor.estado.in_(["disponible", "ocupado", "activo"])
        ).all()

        # Si hoy es VIERNES (4), SÁBADO (5) o DOMINGO (6)
        if dia_semana >= 4:
            for c in conductores_aptos:
                # Verificamos si ya tiene cargada la semana de hoy
                existe = CuotaSemanal.query.filter_by(
                    conductor_id=c.id_conductor, 
                    semana_anio=semana_hoy
                ).first()

                if not existe:
                    # 1. Definimos primero la variable
                    tipo_novedad_actual = 'PAGO_NORMAL' 
                    monto_a_cargar = MONTO_CUOTA_SEMANAL

                    # 2. Ahora sí podemos evaluarla
                    if tipo_novedad_actual == 'INGRESO_TARDIO':
                        monto_a_cargar = 0
                    # Cargamos la cuota automáticamente sin intervención humana
                    nueva_cuota = CuotaSemanal(
                        conductor_id=c.id_conductor,
                        semana_anio=semana_hoy,
                        monto_fijo=monto_a_cargar,
                        pagado=False,
                        tipo_novedad=tipo_novedad_actual
                    )
                    db.session.add(nueva_cuota)
            db.session.commit() # Guardamos los nuevos cargos antes de calcular saldos
        # --------------------------------------------------
        
        resultado = []
        for c in conductores_aptos:
            try:
                # 1. Sumamos TODOS los cargos históricos
                total_cargos = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
                    .filter(CuotaSemanal.conductor_id == c.id_conductor).scalar() or 0.0
                
                # 2. Sumamos TODOS los abonos históricos
                total_abonos = db.session.query(db.func.sum(PagoCuota.monto_pagado))\
                    .filter(PagoCuota.conductor_id == c.id_conductor).scalar() or 0.0

                saldo_real = total_cargos - total_abonos
                
                # Regla para nuevos: Si no tiene registros, su deuda base es la cuota actual
                if total_cargos == 0 and total_abonos == 0:
                    saldo_real = float(MONTO_CUOTA_SEMANAL)

                esta_realmente_solvente = (saldo_real <= 0)
                saldo_mostrar = max(0, saldo_real)

                resultado.append({
                    "id_conductor": c.id_conductor,
                    "unidad": c.codigo,
                    "conductor": c.nombre,
                    "saldo": f"{saldo_mostrar:,.2f}",
                    "pagado": esta_realmente_solvente,
                    "status_html": (
                        '<span class="px-2 py-1 rounded bg-green-100 text-green-700 font-bold text-xs">SOLVENTE</span>' 
                        if esta_realmente_solvente else 
                        '<span class="px-2 py-1 rounded bg-red-100 text-red-700 font-bold text-xs">DEUDOR</span>'
                    )
                })
            except Exception as e:
                print(f"⚠️ Error en datos de {c.nombre}: {str(e)}")
                continue 

        resultado.sort(key=lambda x: float(x['saldo'].replace(',', '')), reverse=True)
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
        # Si el monto está vacío, lo tratamos como 0.0
        monto_total = float(data.get('monto') or 0.0) 
        semana_inicio = int(data.get('semana_inicio', 1)) 
        referencia = data.get('referencia_pago', 'NIVELACIÓN INICIAL')

        id_usuario_jwt = get_jwt_identity()
        ahora = datetime.now()
        
        # 1. Determinamos la semana actual (hoy es 20)
        semana_actual_num = int(ahora.strftime('%U')) 
        semana_actual_label = ahora.strftime('%Y-%U')

        # --- PASO 1: GENERACIÓN DE ESTRUCTURA INTEGRAL (RELLENA HUECOS) ---
        # --- DENTRO DE carga_inicial_pagos ---
        for sem in range(1, semana_actual_num + 1):
            label_busqueda = f"2026-{sem:02d}"
            
            # Buscamos si la semana existe
            existe = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id, 
                semana_anio=label_busqueda
            ).first()
            
            # SI NO EXISTE, LA CREAMOS (Aquí es donde entran la 16, 17 y 18)
            if not existe:
                if sem < semana_inicio:
                    # Estas son las de antes de que entrara a la linea
                    monto_cuota = 0.0
                    esta_pagado = True
                    es_exon = True
                else:
                    # ESTO ES LO QUE IMPORTA: Semanas de trabajo real
                    from app import MONTO_CUOTA_SEMANAL # Asegúrese de que sea 40000
                    monto_cuota = 40000.0 
                    esta_pagado = False
                    es_exon = False

                nueva_cuota = CuotaSemanal(
                    conductor_id=conductor_id,
                    semana_anio=label_busqueda,
                    monto_fijo=monto_cuota,
                    pagado=esta_pagado,
                    es_exonerado=es_exon,
                    tipo_novedad='INGRESO_TARDIO' if es_exon else 'PAGO_NORMAL'
                )
                db.session.add(nueva_cuota)
    
            # OPCIONAL: SI YA EXISTE PERO ES UNA SEMANA DE TRABAJO (>= semana_inicio), 
            # asegurémonos de que el monto sea 40k y no 0 por error.
            elif sem >= semana_inicio and existe.monto_fijo == 0:
                from app import MONTO_CUOTA_SEMANAL
                existe.monto_fijo = MONTO_CUOTA_SEMANAL
                existe.es_exonerado = False
                existe.pagado = False

        # --- PASO 2: REGISTRO DEL ABONO (Si el usuario metió dinero) ---
        if monto_total > 0:
            nuevo_abono = PagoCuota(
                conductor_id=conductor_id,
                semana_anio=semana_actual_label,
                monto_pagado=monto_total,
                metodo_pago='Efectivo',
                referencia=referencia,
                usuario_id=id_usuario_jwt,
                fecha_pago=ahora
            )
            db.session.add(nuevo_abono)

        db.session.commit()

        return jsonify({
            "status": "success",
            "msg": f"✅ Estructura generada. Exonerado hasta Sem {semana_inicio-1}. Abono de {monto_total} registrado."
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error crítico en nivelación: {str(e)}") 
        return jsonify({"error": str(e)}), 500