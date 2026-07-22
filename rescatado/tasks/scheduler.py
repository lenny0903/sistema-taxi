# tasks/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
#from models.despachos import Despacho
scheduler = BackgroundScheduler()
_app = None
_socketio = None

def iniciar_scheduler(app, socketio):
    """Inicializa el scheduler con referencias al app y socketio."""
    global _app, _socketio
    _app = app
    _socketio = socketio

    scheduler.add_job(
        job_verificar_reservas,
        trigger="interval",
        minutes=5,
        id="verificar_reservas",
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    print("✅ Scheduler inicializado cada 5 minutos")

def job_verificar_reservas():
    """Envuelve la verificación dentro del contexto de Flask."""
    if _app is None or _socketio is None:
        print("⚠️ Scheduler no inicializado con app/socketio")
        return

    with _app.app_context():
        try:
            from models.reserva import Reserva
        except Exception as e:
            print("❌ Error importando Reserva:", e)
            return

        reservas = Reserva.query.filter_by(estado="activo").all()
        print(f"🔎 Job ejecutado: {len(reservas)} reservas activas encontradas")

        for r in reservas:
            _socketio.emit("reserva_activa", {
                "id_reserva": r.id_reserva,
                "cliente": getattr(r.cliente, "nombre", ""),
                "origen": r.origen,
                "destino": r.destino,
                # ✅ Conversión segura
                "fecha": r.fecha.isoformat() if r.fecha else None,
                "hora": r.hora.strftime("%H:%M:%S") if r.hora else None
            })

def job_verificar_despachos():
    """Verifica despachos activos y los emite vía Socket.IO."""
    if _app is None or _socketio is None:
        print("⚠️ Scheduler no inicializado con app/socketio")
        return

    with _app.app_context():
        try:
            from models.despachos import Despacho
        except Exception as e:
            print("❌ Error importando Despacho:", e)
            return

        despachos = Despacho.query.filter_by(estado="activo").all()
        print(f"🔎 Job ejecutado: {len(despachos)} despachos activos encontrados")

        for d in despachos:
            # ✅ Usar to_dict() para blindar la serialización
            _socketio.emit("despacho_activo", d.to_dict())

