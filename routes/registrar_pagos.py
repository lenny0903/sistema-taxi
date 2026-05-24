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



@pagos_bp.route('/registrar', methods=['POST'])
@pagos_bp.route('/registrar_pago_ordinario', methods=['POST'])
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
    
    # 🎯 EVOLUCIÓN MULTIAÑO DINÁMICA
    anio_actual = ahora.year
    semana_actual = ahora.strftime('%Y-%U') 

    # Capturamos la semana que el usuario eligió en el select dinámico
    semana_seleccionada = data.get('semana_anio')

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

        # 🧠 AJUSTE QUIRÚRGICO: Si es exoneración en taquilla, el input manda 40k pero contablemente entra 0 a caja
        monto_a_pagar = 0.0 if es_exoneracion else float(data.get('monto_pagado') or MONTO_FIJO_VAL) 

        # =========================================================================
        # 🚨 ADUANAS DE CONTROL Y VALIDACIÓN DE TAQUILLA (MANTENIDAS)
        # =========================================================================
        
        # 1️⃣ Coherencia en Exoneraciones (Evitar dinero en condonaciones)
        if es_exoneracion and monto_a_pagar > 0.0:
            return jsonify({
                "status": "error", 
                "message": f"❌ Conflicto contable: No se puede registrar un monto de {monto_a_pagar} COP para una Exoneración."
            }), 400

        # 2️⃣ Monto mínimo en Pagos Normales
        if not es_exoneracion and monto_a_pagar <= 0.0:
            return jsonify({
                "status": "error", 
                "message": "❌ Monto inválido: El pago de cuotas regulares debe ser mayor a 0 COP."
            }), 400

        # 3️⃣ Múltiplos Exactos (Solo cuando no se selecciona una semana y es abono general)
        if not es_exoneracion and not semana_seleccionada:
            if monto_a_pagar % MONTO_FIJO_VAL != 0:
                return jsonify({
                    "status": "error", 
                    "message": f"❌ Monto fraccionado rechazado: Para abonos generales, el valor debe ser un múltiplo exacto de la tarifa semanal ({int(MONTO_FIJO_VAL)} COP)."
                }), 400
                
        # 4️⃣ Control de Sobrepago (Prevenir saldos fantasmas en el ciclo actual)
        if not es_exoneracion and not semana_seleccionada:
            total_deudas_pendientes = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id,
                pagado=False
            ).filter(
                CuotaSemanal.monto_fijo > 0,
                CuotaSemanal.semana_anio.like(f"{anio_actual}-%")
            ).count()
            
            maximo_a_recibir = total_deudas_pendientes * MONTO_FIJO_VAL
            if monto_a_pagar > maximo_a_recibir:
                return jsonify({
                    "status": "error", 
                    "message": f"❌ Sobrepago detectado: El conductor solo presenta deudas por un total de {int(maximo_a_recibir)} COP para el ciclo {anio_actual}."
                }), 400

        # --- PASO 1: REGISTRAR EL ABONO (O EXONERACIÓN) ---
        # 🎯 AJUSTE: Guardamos en PagoCuota la semana que realmente se está afectando
        semana_registro_log = semana_seleccionada if semana_seleccionada else semana_actual

        nuevo_pago = PagoCuota(
            conductor_id=conductor_id,
            semana_anio=semana_registro_log, 
            monto_pagado=monto_a_pagar,
            metodo_pago=metodo,
            referencia=referencia_limpia,
            usuario_id=id_usuario_jwt,
            fecha_pago=ahora
        )
        db.session.add(nuevo_pago)
        db.session.flush() 

        # --- PASO 2: CALCULAR TOTAL ---
        total_pagado = db.session.query(func.sum(PagoCuota.monto_pagado)).filter(
            PagoCuota.conductor_id == conductor_id,
            PagoCuota.semana_anio == semana_registro_log
        ).scalar() or 0

        # --- PASO 3: LÓGICA DE SOLVENCIA (CASCADA O EXONERACIÓN) ---
        if es_exoneracion:
            # Si es exoneración, actuamos sobre la semana seleccionada en el formulario
            semana_target = semana_seleccionada if semana_seleccionada else semana_actual

            cuota_control = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id, 
                semana_anio=semana_target
            ).first()

            if not cuota_control:
                cuota_control = CuotaSemanal(
                    conductor_id=conductor_id,
                    semana_anio=semana_target,
                    monto_fijo=MONTO_FIJO_VAL
                )
                db.session.add(cuota_control)
            
            cuota_control.pagado = True  
            cuota_control.es_exonerado = True
            cuota_control.tipo_novedad = tipo_novedad
            cuota_control.referencia_pago = referencia_limpia
            cuota_control.fecha_pago = ahora
            cuota_control.monto_pagado = 0.0 # No entra dinero físico
        
        else:
            # SI ES PAGO NORMAL
            
            # 🌊 CASO A: ABONO GENERAL EN CASCADA (Monto global sin semana fija)
            if not semana_seleccionada:
                cuotas_pendientes = CuotaSemanal.query.filter_by(
                    conductor_id=conductor_id, 
                    pagado=False
                ).filter(
                    CuotaSemanal.monto_fijo > 0,
                    CuotaSemanal.semana_anio.like(f"{anio_actual}-%") 
                ).order_by(CuotaSemanal.semana_anio.asc()).all()

                monto_restante = monto_a_pagar
                for cuota in cuotas_pendientes:
                    if monto_restante >= cuota.monto_fijo:
                        cuota.pagado = True
                        cuota.fecha_pago = ahora
                        cuota.referencia_pago = referencia_limpia
                        cuota.tipo_novedad = 'PAGO_NORMAL'
                        cuota.monto_pagado = cuota.monto_fijo
                        monto_restante -= cuota.monto_fijo
                    else:
                        break
            
            # 🎯 CASO B: PAGO DIRIGIDO DESDE EL SELECT (¡SIN VACIÓS CONTABLES!)
            else:
                cuota = CuotaSemanal.query.filter_by(
                    conductor_id=conductor_id, 
                    semana_anio=semana_seleccionada
                ).first()

                if cuota:
                    cuota.pagado = True
                    cuota.fecha_pago = ahora
                    cuota.referencia_pago = referencia_limpia
                    cuota.tipo_novedad = 'PAGO_NORMAL'
                    cuota.monto_pagado = MONTO_FIJO_VAL # Liquidada por completo
                else:
                   # 🎯 Si la celda no existía por deudas de sistema, la creamos solvente
                    nueva_cuota = CuotaSemanal(
                        conductor_id=conductor_id,
                        semana_anio=semana_seleccionada,
                        monto_fijo=MONTO_FIJO_VAL,  # La cuota vale 40k de ley
                        pagado=True,                # Queda saldada a futuro
                        tipo_novedad='PAGO_NORMAL'  # Mantiene la auditoría limpia
                        
                        # ❌ REMOVIDOS por pertenecer a PagoCuota:
                        # fecha_pago=ahora,
                        # referencia_pago=referencia_limpia,
                        # monto_pagado=MONTO_FIJO_VAL
                    )
                    db.session.add(nueva_cuota)

        # FINALIZAMOS TRANSACCIÓN ORIGINAL
        db.session.commit()
        db.session.refresh(nuevo_pago) 

        from models.conductores import Conductor
        c = Conductor.query.get(conductor_id)

        return jsonify({
            "status": "success", 
            "id": nuevo_pago.id,
            "message": "✅ Registro exitoso",
            "monto": nuevo_pago.monto_pagado,
            "conductor": c.nombre if c else "Desconocido",         
            "unidad": c.codigo if c else "N/A",            
            "semana": nuevo_pago.semana_anio,
            "es_exoneracion": es_exoneracion 
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
        
        # 💡 Usamos %V (ISO 8601) para que el cambio de semana sea de lunes a domingo,
        # encajando a la perfección con sus cortes reales de los viernes.
        semana_hoy = ahora.strftime('%Y-%V')
        
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
                    tipo_novedad_actual = 'PAGO_NORMAL' 
                    monto_a_cargar = MONTO_CUOTA_SEMANAL

                    if tipo_novedad_actual == 'INGRESO_TARDIO':
                        monto_a_cargar = 0
                    
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
                # 📊 1. AUDITORÍA CRONOLÓGICA REAL (Basada en el Reloj)
                anio_actual = ahora.strftime('%Y')
                semana_actual_calendario = int(ahora.strftime('%V'))
                if semana_actual_calendario == 0:
                    semana_actual_calendario = 1

                # 2. Contamos estrictamente cuántas semanas del año actual están pagadas en la BD
                semanas_saldadas = CuotaSemanal.query.filter(
                    CuotaSemanal.conductor_id == c.id_conductor, 
                    CuotaSemanal.pagado == True,
                    CuotaSemanal.semana_anio.like(f"{anio_actual}-%")
                ).count()

                # 3. La meta obligatoria a la fecha actual
                semanas_totales = semana_actual_calendario

                # 4. Saldo en mora real (Dinero estricto de celdas vencidas que debe en la taquilla)
                saldo_en_mora = db.session.query(db.func.sum(CuotaSemanal.monto_fijo))\
                    .filter(
                        CuotaSemanal.conductor_id == c.id_conductor,
                        CuotaSemanal.semana_anio <= semana_hoy, # Solo del presente hacia el pasado
                        CuotaSemanal.pagado == False
                    ).scalar() or 0.0

                # 5. Regla de oro para nuevos ingresos (Conductores vírgenes sin movimientos)
                # Buscamos si tiene alguna transacción real en el sistema
                tiene_movimientos = CuotaSemanal.query.filter_by(conductor_id=c.id_conductor).first()
                if not tiene_movimientos:
                    saldo_mostrar_str = f"{MONTO_CUOTA_SEMANAL:,.2f}"
                    metrica_semanas = "0 / 1"
                    esta_solvente = False
                    status_html = '<span class="px-2 py-1 rounded bg-red-100 text-red-700 font-bold text-xs">DEUDOR</span>'
                
                else:
                    # 🧮 MATEMÁTICA CONTABLE DETERMINISTA
                    # Evaluamos si el chofer pagó más allá de la meta del calendario actual
                    if semanas_saldadas > semanas_totales:
                        # Caso: ADELANTADO
                        cuotas_adelantadas = semanas_saldadas - semanas_totales
                        monto_favor = float(cuotas_adelantadas * MONTO_CUOTA_SEMANAL)
                        
                        metrica_semanas = f"{semanas_saldadas} / {semanas_totales}"
                        saldo_mostrar_str = f"-{monto_favor:,.2f}"
                        esta_solvente = True
                        status_html = '<span class="px-2 py-1 rounded bg-blue-100 text-blue-700 font-bold text-xs">ADELANTADO</span>'
                    
                    elif semanas_saldadas == semanas_totales:
                        # Caso: SOLVENTE EXACTO
                        metrica_semanas = f"{semanas_saldadas} / {semanas_totales}"
                        saldo_mostrar_str = "0.00"
                        esta_solvente = True
                        status_html = '<span class="px-2 py-1 rounded bg-green-100 text-green-700 font-bold text-xs">SOLVENTE</span>'
                    
                    else:
                        # Caso: DEUDOR (Tiene semanas rezagadas)
                        # El saldo se calcula multiplicando las semanas que le faltan por la tarifa
                        semanas_debe = semanas_totales - semanas_saldadas
                        saldo_calculado = float(semanas_debe * MONTO_CUOTA_SEMANAL)
                        
                        metrica_semanas = f"{semanas_saldadas} / {semanas_totales}"
                        saldo_mostrar_str = f"{saldo_calculado:,.2f}"
                        esta_solvente = False
                        status_html = '<span class="px-2 py-1 rounded bg-red-100 text-red-700 font-bold text-xs">DEUDOR</span>'

                resultado.append({
                    "id_conductor": c.id_conductor,
                    "unidad": c.codigo,
                    "conductor": c.nombre,
                    "saldo": saldo_mostrar_str,          
                    "semanas_progreso": metrica_semanas,  
                    "pagado": esta_solvente,
                    "status_html": status_html  
                })
                
            except Exception as e:
                print(f"⚠️ Error en datos de {c.nombre}: {str(e)}")
                continue 

        # Ordenamos la respuesta resguardando el formato numérico
        resultado.sort(key=lambda x: float(x['saldo'].replace(',', '').replace('-', '') if '-' in x['saldo'] else x['saldo'].replace(',', '')), reverse=True)
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

@pagos_bp.route('/carga_inicial_pagos', methods=['POST'])
@jwt_required()
def carga_inicial_pagos():
    try:
        # 1️⃣ UNA SOLA LECTURA DEL JSON (Unificamos en 'data')
        data = request.get_json()
        conductor_id = data.get('conductor_id')
        monto_disponible = float(data.get('monto') or 0.0) 
        semana_inicio_front = int(data.get('semana_inicio', 1)) 
        es_exonerated_front = data.get('es_exonerado') # 'SI' o 'NO'
        referencia = data.get('referencia_pago') or "NIVELACIÓN INICIAL"
        
        ahora = datetime.now()
        semana_actual_num = int(ahora.strftime('%V'))
        if semana_actual_num == 0:
            semana_actual_num = 1
        año_actual = datetime.now().year    
        
        from app import MONTO_CUOTA_SEMANAL
        TARIFA_SEMANAL = float(MONTO_CUOTA_SEMANAL)

        # =========================================================================
        # 🛡️ EL CANDADO DEFINITIVO DE LA LÓGICA DE NEGOCIO (REFORMADO CON SU REGLA)
        # =========================================================================
        # 📅 Detectamos la clave estricta de la primera semana del año actual
        año_actual = datetime.now().year
        semana_uno_label = f"{año_actual}-01"

        # Buscamos qué hay registrado en la casilla de la Semana 1
        registro_semana_uno = CuotaSemanal.query.filter_by(
            conductor_id=conductor_id,
            semana_anio=semana_uno_label
        ).first()

        # También verificamos si el conductor ya tiene un ingreso tardío asentado en su historia para la deducción posterior
        ya_tiene_exoneracion = CuotaSemanal.query.filter_by(
            conductor_id=conductor_id,
            tipo_novedad='INGRESO_TARDIO'
        ).first()

        if es_exonerated_front == 'SI':
            # 🎯 REGLA DEL INGENIERO: Si la semana 1 ya existe y NO es un ingreso tardío (es decir, fue pagada o es cuota ordinaria), NO califica.
            if registro_semana_uno and registro_semana_uno.tipo_novedad != 'INGRESO_TARDIO':
                return jsonify({
                    "error": "Operación Denegada: El conductor registra actividad ordinaria en la Semana 01. No califica para Ingreso Tardío."
                }), 400
                
            # 🚨 Doble seguro pasivo: Si ya tiene registros de ingreso tardío y no se quiere sobreescribir
            if ya_tiene_exoneracion is not None:
                # Opcional: Puede dejar que re-exonere si se equivocó, o bloquearlo. 
                # Si prefiere permitir correcciones, simplemente comente estas dos líneas:
                return jsonify({
                    "error": "Operación Denegada: Este conductor ya tiene una exoneración de ingreso asentada."
                }), 400
        else:
            # 🚨 SI VA A METER PLATA ("NO"): Bloqueamos si la semana 1 ya está pagada como ordinaria
            if registro_semana_uno and registro_semana_uno.pagado and registro_semana_uno.tipo_novedad == 'CUOTA_ORDINARIA':
                return jsonify({
                    "error": "Operación Denegada: El conductor ya tiene pagos ordinarios registrados en la taquilla."
                }), 400
        # =========================================================================
        
        # -------------------------------------------------------------------------
        # 🧠 DEDUCCIÓN DE LA SEMANA DE ARRANQUE REAL (SU LÓGICA INTELIGENTE)
        # -------------------------------------------------------------------------
        # Reutilizamos la consulta exacta que ya busca la última exonerada
        ultima_exonerada = ya_tiene_exoneracion if ya_tiene_exoneracion else CuotaSemanal.query.filter_by(
            conductor_id=conductor_id,
            tipo_novedad='INGRESO_TARDIO'
        ).order_by(CuotaSemanal.semana_anio.desc()).first()

        if es_exonerated_front == 'NO':
            if ultima_exonerada is not None:
                # El pasado perdonado llega hasta la semana 9, arrancamos en la 10
                semana_año_str = ultima_exonerada.semana_anio.split('-')[1] 
                semana_arranque_real = int(semana_año_str) + 1
            else:
                # Es un conductor fundador limpio, arranca desde el principio
                semana_arranque_real = 1
        else:
            # Si el operador escogió SI, se respeta la semana seleccionada en la UI
            semana_arranque_real = semana_inicio_front

        # =========================================================================
        # 🔄 PASO 1: GENERACIÓN O RESPETO DE LA MATRIZ DE DEUDAS
        # =========================================================================
        for sem in range(1, semana_actual_num + 1):
            label = f"{año_actual}-{sem:02d}" 
            
            existe = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id, 
                semana_anio=label
            ).first()

            # 🎯 CORREGIDO: Evaluamos usando la semana_arranque_real deducida
            es_antes_de_ingreso = sem < semana_arranque_real
                                
            if es_antes_de_ingreso:
                monto_calculado = 0.0
                pago_status = True  
                exonerado_status = True
                novedad = 'INGRESO_TARDIO'
            else:
                monto_calculado = TARIFA_SEMANAL
                pago_status = False 
                exonerado_status = False
                novedad = 'CUOTA_ORDINARIA'

            if not existe:
                nueva = CuotaSemanal(
                    conductor_id=conductor_id,
                    semana_anio=label,
                    monto_fijo=monto_calculado,
                    pagado=pago_status,
                    tipo_novedad=novedad,
                    es_exonerado=exonerado_status
                )
                db.session.add(nueva)
            else:
                # 🛡️ ESCUDO PROTECTOR INTEGRAL: Las semanas 1 a 9 se quedan intactas
                if not existe.pagado and not existe.es_exonerado:  
                    existe.monto_fijo = monto_calculado
                    existe.pagado = pago_status
                    existe.tipo_novedad = novedad
                    existe.es_exonerado = exonerado_status
            
        db.session.flush()

        # =========================================================================
        # 💰 PASO 2: AMORTIZACIÓN INTELIGENTE DEL SALDO
        # =========================================================================
        if monto_disponible > 0.0:
            cuotas_a_pagar = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id, 
                pagado=False
            ).filter(CuotaSemanal.monto_fijo > 0).order_by(CuotaSemanal.semana_anio.asc()).all()

            print(f"🔬 [CONVERGENCIA] Abonando {monto_disponible} COP a partir de la primera semana pendiente.")

            for cuota in cuotas_a_pagar:
                if monto_disponible >= cuota.monto_fijo:
                    cuota.pagado = True
                    cuota.fecha_pago = ahora
                    cuota.referencia_pago = referencia
                    monto_disponible -= cuota.monto_fijo
                else:
                    break

        db.session.commit()
        return jsonify({"status": "success", "msg": "Nivelación y abono procesados correctamente."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@jwt_required()
def obtener_semanas_pendientes(conductor_id):
    # Traemos TODO lo que no esté pago y que cueste dinero (>0)
    pendientes = CuotaSemanal.query.filter(
        CuotaSemanal.conductor_id == conductor_id,
        CuotaSemanal.pagado == False,
        CuotaSemanal.monto_fijo > 0
    ).order_by(CuotaSemanal.semana_anio.asc()).all()
    
    # 💡 DEBUG CRUCIAL: Mira tu terminal de Flask cuando cargues a Nevis
    print(f"DEBUG: Para el ID {conductor_id} encontré {len(pendientes)} semanas en DB")
    
    return jsonify([{"semana_anio": p.semana_anio, "monto": p.monto_fijo} for p in pendientes])

@pagos_bp.route('/semanas_pendientes/<int:conductor_id>', methods=['GET'])
def obtener_semanas_pendientes_taquilla(conductor_id):
    try:
        # 🎯 BASE DEFENSIVA: Por defecto, no es un pago adelantado
        es_pago_adelantado = False

        # 1. Buscamos primero si tiene semanas colgadas (Lógica Original)
        cuotas = CuotaSemanal.query.filter_by(
            conductor_id=conductor_id,
            pagado=False
        ).filter(CuotaSemanal.tipo_novedad != 'INGRESO_TARDIO').order_by(CuotaSemanal.semana_anio.asc()).all()

        semanas_list = [c.semana_anio for c in cuotas]

        # 💡 [NUEVO] SI NO TIENE DEUDAS: Preparamos el terreno para el pago adelantado
        if not semanas_list:
            es_pago_adelantado = True # Si la lista de deudas está vacía, confirmamos que es adelanto
            
            # Buscamos cuál fue la ÚLTIMA semana que pagó en su historial total
            ultima_cuota_paga = CuotaSemanal.query.filter_by(
                conductor_id=conductor_id,
                pagado=True
            ).order_by(CuotaSemanal.semana_anio.desc()).first()

            if ultima_cuota_paga:
                # Extraemos el año y el número de semana (Ej: "2026-20" -> 2026, 20)
                partes = ultima_cuota_paga.semana_anio.split('-')
                anio = int(partes[0])
                num_semana = int(partes[1])

                # Incrementamos a la semana siguiente para el adelanto
                siguiente_semana = num_semana + 1
                
                # Control básico de fin de año (Si pasa de la 52, saltamos al siguiente año)
                if siguiente_semana > 52:
                    anio += 1
                    siguiente_semana = 1

                # Formateamos la semana futura exacta (Ej: "2026-21")
                semana_adelanto = f"{anio}-{siguiente_semana:02d}"
                semanas_list.append(semana_adelanto)
            else:
                # Escenario de respaldo extremo: Si no tiene ninguna cuota en el sistema,
                # le ofrecemos la semana actual del calendario real
                semanas_list.append(datetime.now().strftime('%Y-%U'))

        # Retornamos el JSON perfectamente estructurado para el JS
        return jsonify({
            "semanas": semanas_list,
            "es_adelanto": es_pago_adelantado  
        }), 200

    except Exception as e:
        print(f"❌ Error en semanas_pendientes para ID {conductor_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500


