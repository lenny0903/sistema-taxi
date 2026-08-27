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
    scheduler.add_job(
        job_verificar_gps_conductores,
        trigger="interval",
        minutes=3, 
        id="job_gps_conductores",
        replace_existing=True
    )
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

def job_verificar_gps_conductores():
    """
    Monitorea de forma proactiva el GPS de los conductores activos.
    Fase 1: Envía un pulso silencioso (sendChatAction) si supera el umbral de silencio.
    Fase 2: Resetea el aviso automáticamente en cuanto el GPS vuelve a reportar.
    """
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.conductores import Conductor
            from extensions import db
            from utils.time import hora_local, TZ_CARACAS

            ahora = hora_local()

            conductores_candidatos = Conductor.query.filter(
                Conductor.telegram_id.isnot(None),
                Conductor.estado == 'activo',
                Conductor.ultima_actualizacion.isnot(None)
            ).all()

            for c in conductores_candidatos:
                # Normalización estricta de ultima_actualizacion
                ult_act = c.ultima_actualizacion
                if ult_act and ult_act.tzinfo is None:
                    ult_act = ult_act.replace(tzinfo=TZ_CARACAS)

                # Tolerancia dinámica individual (por defecto 5 o 15 minutos según configures)
                tolerancia_minutos = getattr(c, 'tolerancia_dinamica_minutos', 5) or 5
                limite_inactividad = ahora - timedelta(minutes=tolerancia_minutos)

                # 🟢 RECUPERACIÓN AUTOMÁTICA: Si el conductor reportó recientemente, reseteamos el candado y la red
                if ult_act >= limite_inactividad:
                    cambios_necesarios = False
                    if getattr(c, 'aviso_enviado', 0) == 1:
                        c.aviso_enviado = 0
                        cambios_necesarios = True
                    if getattr(c, 'estado_red', 'conectado') != 'conectado':
                        c.estado_red = 'conectado'
                        cambios_necesarios = True
                        
                    if cambios_necesarios:
                        db.session.commit()
                    continue  # Todo bien, pasamos al siguiente

                # 🟡 SILENCIO SOSPECHOSO: Superó el umbral y NO se le ha dado el pulso todavía (aviso_enviado == 0)
                if ult_act < limite_inactividad and getattr(c, 'aviso_enviado', 0) == 0:
                    
                    # 🚀 PULSO SILENCIOSO DE DESPIERTE (Acción 'typing' en Telegram, 0 spam visual)
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
                    payload = {
                        "chat_id": c.telegram_id,
                        "action": "typing"
                    }
                    
                    try:
                        res = requests.post(url, json=payload, timeout=4)
                        if res.status_code == 200:
                            # Candado en 1 y red conectada (Telegram confirmó entrega)
                            c.aviso_enviado = 1
                            c.estado_red = 'conectado'
                            db.session.commit()
                            print(f"📡 [PULSO GPS] Latido silencioso enviado a Unidad {c.codigo}")
                        else:
                            # Telegram respondió con un código distinto a 200
                            c.estado_red = 'sin_respuesta'
                            db.session.commit()
                            print(f"⚠️ [PULSO GPS] Telegram rechazó pulso para Unidad {c.codigo} (Status {res.status_code})")
                    except Exception as ex:
                        # Error de red, timeout o fallo al conectar con la API
                        c.estado_red = 'sin_respuesta'
                        db.session.commit()
                        print(f"⚠️ [ERROR PULSO TELEGRAM] Unidad {c.codigo}: {ex}")

            

        except Exception as e:
            from extensions import db
            db.session.rollback()
            print(f"❌ [SCHEDULER ERROR - GPS PROACTIVO] {e}")