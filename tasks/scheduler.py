from apscheduler.schedulers.background import BackgroundScheduler
# 1. Aquí se importan
from datetime import datetime, timedelta

scheduler = BackgroundScheduler(daemon=True)
_app = None
_socketio = None

def iniciar_scheduler(app, socketio):
    global _app, _socketio
    _app = app
    _socketio = socketio
    
    # Limpiamos para evitar duplicados en reinicios de NSSM
    scheduler.remove_all_jobs()
    
    # 1. Tarea de Reservas (Cada 5 segundos)
    scheduler.add_job(
        job_verificar_reservas,
        trigger="interval",
        seconds=5, 
        id="job_reservas"
    )

    # 2. Tarea de Carga de Cuota Semanal (Cada Viernes a las 6:00 AM)
    # Se usa 'cron' para que sea un día y hora específicos
    scheduler.add_job(
        job_cargar_cuotas_semanales, # Asegúrate de haber definido esta función
        trigger="cron",
        day_of_week="fri", # Viernes
        hour=6,
        minute=0,
        id="job_cuota_semanal",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        
    print("🚀 [SISTEMA] Scheduler iniciado: Reservas (5s) y Cuota Semanal (Viernes 6AM)")
def job_verificar_reservas():
    # 2. AQUÍ SE USA 'datetime' (Esto debería quitar el color gris)
    ahora = datetime.now()
    #print(f"⏰ Revisando base de datos: {ahora.strftime('%H:%M:%S')}")
    
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.reserva import Reserva
            from extensions import db
            
            # 3. AQUÍ SE USA 'timedelta' (Esto también debería quitar el gris)
            margen = ahora + timedelta(minutes=15)

            reservas = Reserva.query.filter_by(estado="activo", notificada=False).all()

            for r in reservas:
                fecha_reserva = datetime.combine(r.fecha, r.hora)
                
                # Si la reserva es en los próximos 15 minutos
                if ahora <= fecha_reserva <= margen:
                    print(f"📢 Avisando reserva #{r.id_reserva}")
                    _socketio.emit("reserva_activa", {
                        "id_reserva": r.id_reserva,
                        "cliente": getattr(r.cliente, "nombre", "Cliente"),
                        "origen": r.origen,
                        "destino": r.destino,
                        "hora": r.hora.strftime("%H:%M")
                    })
                    r.notificada = True
            
            db.session.commit()
        except Exception as e:
            print(f"❌ Error: {e}")
def job_cargar_cuotas_semanales():
    if _app is None:
        return

    with _app.app_context():
        try:
            from flask import current_app # Importamos esto para leer la config
            from models.conductores import Conductor
            from models.registrar_pagos import Pago 
            from extensions import db
            
            # Buscamos el monto directamente de la configuración de la app
            # Asegúrate de que en app.py lo hayas puesto como app.config['MONTO_CUOTA_SEMANAL'] = 40000
            monto = current_app.config.get('MONTO_CUOTA_SEMANAL', 40000)
            
            conductores = Conductor.query.filter_by(activo=True).all()
            
            for c in conductores:
                nueva_deuda = Pago(
                    id_conductor=c.id,
                    monto=-monto,
                    fecha=datetime.now(),
                    descripcion="Cuota Semanal Automática"
                )
                db.session.add(nueva_deuda)
            
            db.session.commit()
            print(f"✅ [CONTABILIDAD] Cuota de {monto} cargada con éxito.")
            _socketio.emit('actualizar_tabla_pagos', {'status': 'success'})

        except Exception as e:
            db.session.rollback()
            print(f"❌ [ERROR CONTABLE] Fallo: {e}")