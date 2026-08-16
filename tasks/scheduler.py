import os
import shutil
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from utils.time import hora_local
from dotenv import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler(daemon=True)
_app = None
_socketio = None

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def ejecutar_respaldo_automatico():
    base_path = os.getcwd()
    ruta_db = os.path.join(base_path, 'taxis.db')
    carpeta_backups = os.path.join(base_path, 'backups_automaticos')
    
    if not os.path.exists(carpeta_backups):
        os.makedirs(carpeta_backups)
    
    nombre_backup = f"taxis_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
    ruta_destino = os.path.join(carpeta_backups, nombre_backup)
    
    try:
        if os.path.exists(ruta_db):
            shutil.copy2(ruta_db, ruta_destino)
            print(f"[OK] [BACKUP] Respaldo generado con éxito: {nombre_backup}")
            gestionar_almacenamiento_backups(carpeta_backups)
        else:
            print(f"[ALERTA] [ERROR] No se encontró la DB en: {ruta_db}")
    except Exception as e:
        print(f"[ERROR] [ERROR BACKUP] Fallo técnico: {e}")

def gestionar_almacenamiento_backups(carpeta):
    backups = sorted([os.path.join(carpeta, f) for f in os.listdir(carpeta)], key=os.path.getmtime)
    while len(backups) > 24:
        os.remove(backups.pop(0))

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
        id="job_reservas",
        replace_existing=True
    )

   # 2. Tarea de Monitoreo de GPS de Conductores (Cada 3 minutos)
 #   scheduler.add_job(
 #       job_verificar_gps_conductores,
 #       trigger="interval",
 #       minutes=3, 
 #       id="job_gps_conductores",
 #       replace_existing=True
 #   )
    scheduler.add_job(
        job_expirar_tiempos_gps,
        trigger="interval",
        minutes=1, 
        id="job_expiracion_gps",
        replace_existing=True
    )
    # 3. Tarea de Respaldos Automáticos (Cada 12 horas)
    scheduler.add_job(
        id='Backup_Cada_12_Horas',
        func=ejecutar_respaldo_automatico,
        trigger='interval',
        hours=12,
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        
    print("🚀 [SISTEMA] Scheduler centralizado activo con Reservas, GPS Adaptativo y Respaldos.")

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

def job_expirar_tiempos_gps():
    """
    Función ligera dedicada exclusivamente a marcar tiempos expirados.
    Se ejecuta independientemente de las alertas de inactividad.
    """
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.conductores import Conductor
            from extensions import db
            from utils.time import hora_local, TZ_CARACAS

            ahora = hora_local()
            
            # Buscamos conductores que tengan expiración, que estén activos y que NO estén ya expirados
            conductores_vencidos = Conductor.query.filter(
                Conductor.expiracion_gps.isnot(None),
                Conductor.opcion_gps != "Expirado",
                Conductor.opcion_gps != "Finalizado"
            ).all()

            for c in conductores_vencidos:
                exp_db = c.expiracion_gps
                if exp_db and exp_db.tzinfo is None:
                    exp_db = exp_db.replace(tzinfo=TZ_CARACAS)

                # Si el tiempo ya pasó, marcamos como Expirado
                if exp_db and ahora >= exp_db:
                    c.opcion_gps = "Expirado"
                    db.session.commit()
                    print(f"⏱️ [GPS EXPIRADO] Unidad {c.codigo} marcada automáticamente como expirada.")
            
        except Exception as e:
            from extensions import db
            db.session.rollback()
            print(f"❌ [ERROR SCHEDULER - VENCIMIENTOS] {e}")
"""
def job_verificar_gps_conductores():
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.conductores import Conductor
            from extensions import db
            from utils.time import TZ_CARACAS

            ahora = hora_local()

            conductores_candidatos = Conductor.query.filter(
                Conductor.telegram_id.isnot(None),
                Conductor.estado == 'activo',
                Conductor.ultima_actualizacion.isnot(None)
            ).all()

            for c in conductores_candidatos:
                # 🛡️ Control Anti-Spam
                if getattr(c, 'alerta_enviada', False): 
                    continue

                # Normalización estricta de expiracion_gps
                exp_db = c.expiracion_gps
                if exp_db and exp_db.tzinfo is None:
                    exp_db = exp_db.replace(tzinfo=TZ_CARACAS)

                # 🛡️ ESCENARIO 1: Expiración natural del cronómetro
                if exp_db is None or ahora >= exp_db:
                    continue

                # Normalización estricta de ultima_actualizacion
                ult_act = c.ultima_actualizacion
                if ult_act and ult_act.tzinfo is None:
                    ult_act = ult_act.replace(tzinfo=TZ_CARACAS)

                # 🚀 TOLERANCIA DINÁMICA INDIVIDUAL
                # Se lee la tolerancia de cada conductor (15 min por defecto si está en None)
                tolerancia_minutos = getattr(c, 'tolerancia_dinamica_minutos', 15) or 15
                limite_inactividad = ahora - timedelta(minutes=tolerancia_minutos)

                # Si reportó dentro de su margen personalizado, no se dispara alerta
                if ult_act >= limite_inactividad:
                    continue  

                # 🛡️ ESCENARIOS 2 y 3: Superó su umbral adaptativo
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": c.telegram_id,
                    "text": (
                        f"🚨 *ALERTA UNIDAD {c.codigo}*\n\n"
                        f"Se ha perdido la señal de tu GPS hace más de {tolerancia_minutos} minutos.\n\n"
                        "📱 *Por favor abre Telegram* un segundo para reactivar tu ubicación en el mapa."
                    ),
                    "parse_mode": "Markdown",
                    "disable_notification": False
                }
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(requests.post, url, json=payload, timeout=5)
                    res = future.result()
                
                if res.status_code == 200:
                    print(f"⚠️ [GPS DESPERTADOR] Notificación enviada a {c.codigo} (Umbral personalizado: {tolerancia_minutos}m)")
                    c.alerta_enviada = True
                    db.session.commit()  
                
            db.session.commit()

        except Exception as e:
            from extensions import db
            db.session.rollback()
            print(f"❌ [SCHEDULER ERROR - GPS] {e}")
"""            