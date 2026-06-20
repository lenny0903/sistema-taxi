from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time # Importante para dar un respiro a la DB

scheduler = BackgroundScheduler(daemon=True)
_app = None
_socketio = None

def iniciar_scheduler(app, socketio):
    global _app, _socketio
    _app = app
    _socketio = socketio
    
    scheduler.remove_all_jobs()
    
    # Tarea de Reservas
    scheduler.add_job(
        job_verificar_reservas,
        trigger="interval",
        seconds=5, 
        id="job_reservas"
    )
    
    if not scheduler.running:
        scheduler.start()
        
    print("🚀 [SISTEMA] Scheduler activo.")

def job_verificar_reservas():
    if _app is None:
        return

    # Usar app_context es el blindaje perfecto
    with _app.app_context():
        try:
            from models.reserva import Reserva
            from extensions import db
            
            ahora = datetime.now()
            margen = ahora + timedelta(minutes=15)

            # Usamos un bloque simple de consulta
            reservas = Reserva.query.filter_by(estado="activo", notificada=False).all()

            for r in reservas:
                # Combinamos fecha y hora de la reserva
                fecha_reserva = datetime.combine(r.fecha, r.hora)
                
                if ahora <= fecha_reserva <= margen:
                    _socketio.emit("reserva_activa", {
                        "id_reserva": r.id_reserva,
                        "cliente": getattr(r.cliente, "nombre", "Cliente"),
                        "origen": r.origen,
                        "destino": r.destino,
                        "hora": r.hora.strftime("%H:%M")
                    })
                    r.notificada = True
            
            # Commit con manejo de excepciones
            db.session.commit()
            
        except Exception as e:
            # Importante: si algo falla, revertir la transacción
            from extensions import db
            db.session.rollback()
            print(f"❌ [SCHEDULER ERROR] {e}")