import os
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from utils.time import hora_local
from dotenv import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler(daemon=True)
_app = None
_socketio = None

# Obtener Token desde variables de entorno o configuración
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def iniciar_scheduler(app, socketio):
    global _app, _socketio
    _app = app
    _socketio = socketio
    
    scheduler.remove_all_jobs()
    
    # 1. Tarea de Reservas (Cada 5 segundos)
    scheduler.add_job(
        job_verificar_reservas,
        trigger="interval",
        seconds=5, 
        id="job_reservas"
    )

    # 2. Tarea de Monitoreo de GPS de Conductores (Cada 3 minutos)
    scheduler.add_job(
        job_verificar_gps_conductores,
        trigger="interval",
        minutes=3, 
        id="job_gps_conductores"
    )
    
    if not scheduler.running:
        scheduler.start()
        
    print("🚀 [SISTEMA] Scheduler activo con monitoreo de GPS.")


def job_verificar_reservas():
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.reserva import Reserva
            from extensions import db
            
            ahora = hora_local()
            margen = ahora + timedelta(minutes=15)

            reservas = Reserva.query.filter_by(estado="activo", notificada=False).all()

            for r in reservas:
                fecha_reserva = datetime.combine(r.fecha, r.hora)
                ahora = hora_local()
                if ahora <= fecha_reserva <= margen:
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
            from extensions import db
            db.session.rollback()
            print(f"❌ [SCHEDULER ERROR - RESERVAS] {e}")


def job_verificar_gps_conductores():
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.conductores import Conductor
            from extensions import db
            from utils.time import TZ_CARACAS

            ahora = hora_local()
            hace_5_minutos = ahora - timedelta(minutes=5)

            # 1. Consulta limpia y segura en la BD (evita el choque de tipos en el filtro SQL)
            conductores_candidatos = Conductor.query.filter(
                Conductor.telegram_id.isnot(None),
                Conductor.estado == 'activo',
                Conductor.ultima_actualizacion.isnot(None)
            ).all()

            for c in conductores_candidatos:
                # 🛡️ Normalización estricta de ultima_actualizacion (por si acaso viene naive de la BD)
                ult_act = c.ultima_actualizacion
                if ult_act and ult_act.tzinfo is None:
                    ult_act = ult_act.replace(tzinfo=TZ_CARACAS)

                # 3. Validar si la señal se cayó hace más de 5 minutos
                if ult_act >= hace_5_minutos:
                    continue  

                # 🛡️ Normalización estricta de expiracion_gps
                exp_db = c.expiracion_gps
                if exp_db and exp_db.tzinfo is None:
                    exp_db = exp_db.replace(tzinfo=TZ_CARACAS)

                # 1. Si expiracion_gps existe y ya expiró, se omite
                if exp_db is not None and exp_db < ahora:
                    continue

                # 2. Validar bandera de alerta enviada para no saturar
                if getattr(c, 'alerta_enviada', False): 
                    continue

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": c.telegram_id,
                    "text": (
                        f"🚨 *ALERTA UNIDAD {c.codigo}*\n\n"
                        "Se ha perdido la señal de tu GPS hace más de 5 minutos.\n\n"
                        "📱 *Por favor abre Telegram* un segundo para reactivar tu ubicación en el mapa."
                    ),
                    "parse_mode": "Markdown",
                    "disable_notification": False
                }
                
                # 👇 ENVOLVER LA PETICIÓN EN UN HILO NATIVO PURO PARA EVITAR EL BLOQUEO DE EVENTLET
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(requests.post, url, json=payload, timeout=5)
                    res = future.result() # Captura el resultado fuera del contexto verde
                
                if res.status_code == 200:
                    print(f"⚠️ [GPS DESPERTADOR] Notificación sonora enviada a {c.codigo}")
                    c.alerta_enviada = True
                
            db.session.commit()

        except Exception as e:
            from extensions import db
            db.session.rollback()
            print(f"❌ [SCHEDULER ERROR - GPS] {e}")