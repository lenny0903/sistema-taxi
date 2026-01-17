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
    
    # Evitar duplicados si el servidor se reinicia solo
    scheduler.remove_all_jobs()
    
    scheduler.add_job(
        job_verificar_reservas,
        trigger="interval",
        seconds=5, # Revisión rápida para pruebas
        id="job_reservas"
    )
    
    if not scheduler.running:
        scheduler.start()
    print("🚀 [SISTEMA] Scheduler activo cada 20 segundos")

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