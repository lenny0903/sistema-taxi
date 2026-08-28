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
    
    # 1. Tarea de Reservas (Cada 60 segundos)
    scheduler.add_job(
        job_verificar_reservas,
        trigger="interval",
        seconds=60, 
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
        minutes=2, 
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
    Monitorea el GPS y valida la conectividad real del servidor con Telegram.
    Si la red está caída (túnel apagado), no da por buenos los timestamps viejos.
    """
    if _app is None:
        return

    with _app.app_context():
        try:
            from models.conductores import Conductor
            from extensions import db
            from utils.time import hora_local, TZ_CARACAS
            import requests

            ahora = hora_local()

            # 🌐 1. TEST RÁPIDO DE CONECTIVIDAD: Verificar si el servidor tiene salida a Telegram
            red_disponible = True
            try:
                # Un getMe rápido con timeout corto para no congelar el hilo
                test_res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=3)
                if test_res.status_code != 200:
                    red_disponible = False
            except Exception:
                red_disponible = False  # No hay internet o el túnel está abajo

            # 🚨 SI LA RED ESTÁ CAÍDA (Túnel apagado)
            if not red_disponible:
                print("⚠️ [ALERTA RED] Servidor sin conexión a Telegram (¿Túnel apagado?). Forzando estado desconectado a la flota.")
                conductores_activos = Conductor.query.filter_by(estado='activo').all()
                for c in conductores_activos:
                    if getattr(c, 'estado_red', 'conectado') == 'conectado':
                        c.estado_red = 'desconectado'
                        db.session.commit()
                return  # Salimos del job para evitar falsos positivos matemáticos

            # 🛑 CANDADO INICIAL BLINDADO: Forzar desconectado si no hay coordenadas ni timestamp
            conductores_sin_gps = Conductor.query.filter(
                Conductor.estado == 'activo',
                (Conductor.ultima_actualizacion.is_(None)) | 
                (Conductor.latitud.is_(None)) | 
                (Conductor.longitud.is_(None))
            ).all()

            for c_sin in conductores_sin_gps:
                if c_sin.estado_red != 'desconectado':
                    c_sin.estado_red = 'desconectado'
                    db.session.commit()

            for c_sin in conductores_sin_gps:
                if getattr(c_sin, 'estado_red', 'conectado') != 'desconectado':
                    c_sin.estado_red = 'desconectado'
                    db.session.commit()

            # --- SI LA RED SÍ ESTÁ ACTIVA, PROCEDEMOS CON EL FLUJO NORMAL ---
            conductores_candidatos = Conductor.query.filter(
                Conductor.telegram_id.isnot(None),
                Conductor.estado == 'activo',
                Conductor.ultima_actualizacion.isnot(None)
            ).all()

            for c in conductores_candidatos:
                ult_act = c.ultima_actualizacion
                if ult_act and ult_act.tzinfo is None:
                    ult_act = ult_act.replace(tzinfo=TZ_CARACAS)

                tolerancia_minutos = getattr(c, 'tolerancia_dinamica_minutos', 5) or 5
                limite_inactividad = ahora - timedelta(minutes=tolerancia_minutos)

                opcion_actual = str(getattr(c, 'opcion_gps', '') or '').strip()
                es_valido_por_estado = opcion_actual not in ["Expirado", "Finalizado", ""]

                # 🛑 REGLA ESTRICTA: Solo se mantiene conectado SI está dentro del tiempo Y el webhook acaba de recibir datos frescos.
                # De lo contrario, el scheduler lo baja a desconectado.
                if ult_act >= limite_inactividad and c.latitud is not None and c.longitud is not None and es_valido_por_estado:
                    # Si cumple, solo limpiamos el aviso si estaba pendiente, pero NO tocamos el estado_red aquí.
                    if getattr(c, 'aviso_enviado', 0) == 1:
                        c.aviso_enviado = 0
                        db.session.commit()
                    continue
                else:
                    # 🔴 FUERZA BRUTA A ROJO: Si pasó la tolerancia o expiró, la red se cae obligatoriamente
                    if getattr(c, 'estado_red', 'conectado') == 'conectado':
                        c.estado_red = 'desconectado'
                        db.session.commit()

                # Si superó el umbral de silencio
                if ult_act < limite_inactividad and getattr(c, 'aviso_enviado', 0) == 0:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
                    payload = {"chat_id": c.telegram_id, "action": "typing"}
                    
                    try:
                        res = requests.post(url, json=payload, timeout=4)
                        if res.status_code == 200:
                            c.aviso_enviado = 1
                            db.session.commit()
                            print(f"📡 [PULSO GPS] Latido silencioso enviado a Unidad {c.codigo}")
                        else:
                            c.estado_red = 'desconectado'
                            c.aviso_enviado = 1
                            db.session.commit()
                    except Exception:
                        c.estado_red = 'desconectado'
                        c.aviso_enviado = 1
                        db.session.commit()

        except Exception as e:
            from extensions import db
            db.session.rollback()
            print(f"❌ [SCHEDULER ERROR - GPS PROACTIVO] {e}")