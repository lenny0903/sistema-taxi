import shutil

import eventlet
from models.matriz_tarifas import MatrizTarifa
from flask_apscheduler import APScheduler
eventlet.monkey_patch() # Recomendado para modo 'eventlet'
from flask_jwt_extended import JWTManager   # <-- importa JWTManager
from flask import Flask, render_template, url_for, redirect
from flask_migrate import Migrate
from extensions import db
import routes
from routes.views import views_bp
from flask import send_from_directory
from models.turnos import Turno
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text 
from sqlalchemy.engine import Engine
from tasks.scheduler import iniciar_scheduler
from datetime import datetime
import os
import config
import sqlite3


from flask_socketio import SocketIO
MONTO_CUOTA_SEMANAL = 40000

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
scheduler = APScheduler() # Instancia global
def ejecutar_respaldo_automatico():
    base_path = os.getcwd()
    # 🛠️ CAMBIO AQUÍ: Eliminamos 'instance' de la ruta
    ruta_db = os.path.join(base_path, 'taxis.db') 
    carpeta_backups = os.path.join(base_path, 'backups_automaticos')
    
    if not os.path.exists(carpeta_backups):
        os.makedirs(carpeta_backups)
    
    nombre_backup = f"taxis_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
    ruta_destino = os.path.join(carpeta_backups, nombre_backup)
    
    try:
        # Verificamos si el archivo realmente existe antes de copiar
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
    while len(backups) > 24: # Guardamos solo un día completo (24 horas)
        os.remove(backups.pop(0))

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    print(" Base conectada:", app.config['SQLALCHEMY_DATABASE_URI'])

    migrate = Migrate(app, db)
    app.secret_key = "clave_super_secreta_unica"  
    socketio.init_app(app)
    db.init_app(app)
    jwt = JWTManager(app)
   
   
    with app.app_context():
        import models
        from models.lista_espera import ListaEspera
        db.create_all()
         # 🔹 Activar WAL mode en cada conexión SQLite
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.close()
         # Verificación opcional
        result = db.session.execute(text("PRAGMA journal_mode;")).scalar() 
        print(" Journal mode actual:", result)

    # 🔹 Inicializar el scheduler con app y socketio (fuera del app_context)
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
    #from routes.lista_espera_multiple import lista_espera_multiple_bp
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
    #app.register_blueprint(lista_espera_multiple_bp, url_prefix="/lista_espera_multiple")
    app.register_blueprint(cola_despachos_bp, url_prefix="/cola_despachos")
    app.register_blueprint(pagos_bp, url_prefix="/pagos")
    app.register_blueprint(incidencias_bp, url_prefix="/incidencias")
    
    print(app.url_map)

    @app.route("/")
    def home():
        # Entrada oficial: siempre carga index.html
        return render_template("index.html")

    @app.route("/index.html")
    def index_html():
        # Alias opcional, también carga index.html
        return render_template("index.html")

    @app.route("/login")
    def login_redirect():
        # Si alguien entra a /login, lo mandamos al login oficial
        return redirect(url_for("home"))

    @app.route("/panel.html")
    def panel_html():
        # Obtenemos las tarifas y las convertimos a una lista de diccionarios
        tarifas = MatrizTarifa.query.all()
        destinos_lista = [
            {
                "destino": t.destino, 
                "precio_cop": t.precio_cop, 
                "municipio": t.municipio
            } for t in tarifas
        ]
    
        # Pasamos la lista procesada al template
        return render_template("dashboard.html", destinos=destinos_lista)
          
    
    #app.register_blueprint(views_bp)

    return app


if __name__ == "__main__":
   app = create_app()
    
   # 1. Vincular el scheduler a la app
   scheduler.init_app(app)
    
   # 2. Programar la tarea (Cambiado a 1 minuto para tu prueba)
   scheduler.add_job(id='Backup_Prueba', func=ejecutar_respaldo_automatico, trigger='interval', hours=1)
    
   # 3. Iniciar
   scheduler.start()
    
   print("🚀 Servidor y Scheduler iniciados...")
   socketio.run(app, debug=True, host="0.0.0.0", port=5000)