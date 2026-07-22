import sys

# 1. Condicionamos eventlet para que no rompa el contexto de consola al migrar
if 'db' not in sys.argv:
    import eventlet
    eventlet.monkey_patch()

import os
import shutil
import sqlite3
from datetime import datetime, timedelta

# Ahora sí, imports de Flask y extensiones de forma segura
from flask import Flask, jsonify, render_template, url_for, redirect, request, send_from_directory
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from flask_socketio import SocketIO
from sqlalchemy import event, text 
from sqlalchemy.engine import Engine

# Imports de base de datos y modelos locales
from extensions import db
from models.turnos import Turno
from models.matriz_tarifas import MatrizTarifa
from models.cuota_semanal import CuotaSemanal
from models.pago_cuotas import PagoCuota
#from models.operacion_pendiente import OperacionPendiente
import routes
import config
from tasks.scheduler import iniciar_scheduler

MONTO_CUOTA_SEMANAL = 40000

# 2. Inicializamos SocketIO de manera segura según el comando ejecutado
if 'db' not in sys.argv:
    socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
else:
    socketio = SocketIO(cors_allowed_origins="*")

scheduler = APScheduler() # Instancia global

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
            print(f"✅ [BACKUP] Respaldo generado con éxito: {nombre_backup}")
            gestionar_almacenamiento_backups(carpeta_backups)
        else:
            print(f"⚠️ [ERROR] No se encontró la DB en: {ruta_db}")
    except Exception as e:
        print(f"❌ [ERROR BACKUP] Fallo técnico: {e}")

def gestionar_almacenamiento_backups(carpeta):
    backups = sorted([os.path.join(carpeta, f) for f in os.listdir(carpeta)], key=os.path.getmtime)
    while len(backups) > 24: 
        os.remove(backups.pop(0))

def create_app():
    # 1. PRIMERO: Crea la aplicación
    app = Flask(__name__)
    
    # 2. DESPUÉS: Ya puedes usar 'app' para configurar
    app.config.from_object('config')
    
    # 3. Blindaje de seguridad
    LLAVE_FIJA = "taxis_tachira_2026_fija_pro" 
    app.config['SECRET_KEY'] = LLAVE_FIJA
    app.config['JWT_SECRET_KEY'] = LLAVE_FIJA
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    app.config['DEBUG'] = config.DEBUG
    print(" Base conectada:", app.config['SQLALCHEMY_DATABASE_URI'])

    migrate = Migrate(app, db, render_as_batch=True)
    app.migrate = migrate

    from routes.telegram_bot import telegram_bp
    app.register_blueprint(telegram_bp, url_prefix="/telegram")
    socketio.init_app(app)
    db.init_app(app)
    jwt = JWTManager(app)
    app.extensions['jwt'] = jwt
   
    with app.app_context():
        import models
        from models.lista_espera import ListaEspera
        from models.cola_notificaciones import ColaNotificaciones
        #from models.operacion_pendiente import OperacionPendiente
        db.create_all()
        
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.close()

        result = db.session.execute(text("PRAGMA journal_mode;")).scalar() 
        print(" Journal mode actual:", result)

    # 🔹 Inicializar el scheduler condicionado (Evita fallos al correr migraciones)
    if 'db' not in sys.argv:
        iniciar_scheduler(app, socketio)

    # Registrar blueprints...
    from routes.auth import auth_bp
    from routes.usuarios import usuarios_bp
    from routes.roles import roles_bp
    from routes.clientes import clientes_bp
    from routes.conductores import conductores_bp
    from routes.autos import autos_bp
    from routes.despachos import despachos_bp
    from routes.init import init_bp
    from routes.turnos import turnos_bp
    from routes.reportes import reporte_bp
    from routes.lista_espera import lista_espera_bp
    from utils.respaldo import respaldo_bp
    from utils.grupos import grupos_bp
    from routes.reservas import reservas_bp
    from routes.views import views_bp
    from routes.puntos_espera import puntos_bp
    from routes.cola_despachos import cola_despachos_bp
    from routes.registrar_pagos import pagos_bp
    from routes.incidencias import incidencias_bp
    
    app.register_blueprint(init_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(roles_bp, url_prefix="/roles")
    app.register_blueprint(clientes_bp, url_prefix="/clientes")
    app.register_blueprint(conductores_bp, url_prefix="/conductores")
    app.register_blueprint(autos_bp, url_prefix="/autos")
    app.register_blueprint(despachos_bp, url_prefix="/despachos")
    app.register_blueprint(turnos_bp, url_prefix="/turnos")
    app.register_blueprint(lista_espera_bp, url_prefix="/lista_espera")
    app.register_blueprint(reporte_bp, url_prefix="/reportes")
    app.register_blueprint(respaldo_bp, url_prefix="/respaldo")
    app.register_blueprint(grupos_bp, url_prefix="/grupos")
    app.register_blueprint(views_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(puntos_bp)
    app.register_blueprint(cola_despachos_bp, url_prefix="/cola_despachos")
    app.register_blueprint(pagos_bp, url_prefix="/pagos")
    app.register_blueprint(incidencias_bp, url_prefix="/incidencias")
    
    print(app.url_map)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/index.html")
    def index_html():
        return render_template("index.html")

    @app.route("/login")
    def login_redirect():
        return redirect(url_for("home"))

    @app.route("/panel.html")
    def panel_html():
        tarifas = MatrizTarifa.query.all()
        destinos_lista = [
            {
                "destino": t.destino, 
                "precio_cop": t.precio_cop, 
                "municipio": t.municipio
            } for t in tarifas
        ]
        return render_template("dashboard.html", destinos=destinos_lista)

    def configurar_webhook():
        import requests
        TOKEN = "8818215412:AAEFE96X3yOejvx65oRlHVzBkAllIGdXQxg"
        URL_PUBLICA = "https://responsible-brought-flashers-commons.trycloudflare.com"
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={URL_PUBLICA}/telegram/webhook"
        requests.get(url)     
    
    # 🔹 Condicionar la ejecución del scheduler interno para que ignore los comandos 'db'
    if 'db' not in sys.argv:
        scheduler.init_app(app)
        scheduler.add_job(id='Backup_Prueba', func=ejecutar_respaldo_automatico, trigger='interval', hours=24, replace_existing=True)
        scheduler.start()
        print("🚀 Servidor y Scheduler iniciados en modo Producción...")

    return app

if __name__ == "__main__":
    app = create_app()
    print(f"🚀 Servidor iniciado. Debug activado: {app.config['DEBUG']}")
    socketio.run(app, host="0.0.0.0", port=5000)