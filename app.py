from curses import window
import sys
import io

# 0. Forzar UTF-8 absoluto antes de cualquier otra cosa
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 1. Aplicar el parche de eventlet al inicio absoluto
if 'db' not in sys.argv:
    import eventlet
    eventlet.monkey_patch()

# 2. Resto de importaciones
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
import json

from flask import Flask, jsonify, render_template, url_for, redirect, request, send_from_directory, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_apscheduler import APScheduler, json
from flask_socketio import SocketIO
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from extensions import db, socketio
from models.turnos import Turno
from models.matriz_tarifas import MatrizTarifa
from models.cuota_semanal import CuotaSemanal
from models.pago_cuotas import PagoCuota
from models.conductores import Conductor  
from models.clientes import Cliente
import models
import routes
import config
from tasks.scheduler import iniciar_scheduler

# Usamos la constante desde config.py para evitar importaciones circulares
MONTO_CUOTA_SEMANAL = getattr(config, 'MONTO_CUOTA_SEMANAL', 40000)

# Inicializamos SocketIO de manera segura según el comando ejecutado


# 🔥 CONFIGURACIÓN DE LOGGING
import logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 🟢 Función global para el PRAGMA WAL de SQLite
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()

# Bandera de control para evitar registro duplicado del listener
_pragma_listener_registered = False


def create_app():
    global _pragma_listener_registered
    app = Flask(__name__)
    
    app.config.from_object('config')
    
    LLAVE_FIJA = "taxis_tachira_2026_fija_pro"
    app.config['SECRET_KEY'] = LLAVE_FIJA
    app.config['JWT_SECRET_KEY'] = LLAVE_FIJA
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    app.config['DEBUG'] = config.DEBUG
    print("Base conectada:", app.config['SQLALCHEMY_DATABASE_URI'])

    migrate = Migrate(app, db, render_as_batch=True)
    app.migrate = migrate

    from routes.telegram_bot import telegram_bp
    app.register_blueprint(telegram_bp, url_prefix="/telegram")
    socketio.init_app(app)
    db.init_app(app)
    jwt = JWTManager(app)
    app.extensions['jwt'] = jwt

    @app.route('/api/tasa', methods=['GET', 'POST'])
    def gestionar_tasa():
        import json as json_nativo  # 👈 Forzamos el uso del json nativo de Python
        ARCHIVO_TASA = 'tasa_actual.json'
        
        if request.method == 'POST':
            try:
                data = request.get_json(silent=True) or {}
                datos_nuevos = {
                    "tasa_usd_cop": float(data.get('tasa_usd_cop', 4100)),
                    "tasa_cop_ves": float(data.get('tasa_cop_ves', 0.05))
                }
                with open(ARCHIVO_TASA, 'w', encoding='utf-8') as f:
                    json_nativo.dump(datos_nuevos, f)  # 👈 Usamos json_nativo.dump
                return jsonify({"status": "success", **datos_nuevos})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400
        
        if os.path.exists(ARCHIVO_TASA):
            try:
                with open(ARCHIVO_TASA, 'r', encoding='utf-8') as f:
                    return jsonify(json_nativo.load(f))  # 👈 Usamos json_nativo.load
            except:
                pass
                
        return jsonify({"tasa_usd_cop": 4100, "tasa_cop_ves": 0.05})    
    with app.app_context():
        import models
        from models.lista_espera import ListaEspera
        from models.cola_notificaciones import ColaNotificaciones
        db.create_all()
        
        # 🟢 Registro seguro del listener dentro del contexto de la aplicación
        if not _pragma_listener_registered:
            event.listen(db.engine, "connect", set_sqlite_pragma)
            _pragma_listener_registered = True

        result = db.session.execute(text("PRAGMA journal_mode;")).scalar()
        print("Journal mode actual:", result)

    # Registrar blueprints
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
    
    @app.route('/ping', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "ok", 
            "timestamp": datetime.now().isoformat()
        }), 200

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/index.html")
    def index_html():
        return render_template("index.html")

    @app.route("/login")
    def login_redirect():
        return redirect(url_for("home"))

    from routes.views import obtener_url_tunel  
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
        return render_template("dashboard.html", destinos=destinos_lista, dominio_publico=obtener_url_tunel())

    @app.route('/obtener_tarifas', methods=['GET'])
    def obtener_tarifas():
        try:
            tarifas = MatrizTarifa.query.all()
            # Convertimos la lista de objetos de SQLAlchemy a una lista de diccionarios JSON
            return jsonify([
                {
                    "id": t.id, 
                    "destino": t.destino, 
                    "precio_cop": t.precio_cop, 
                    "municipio": t.municipio
                } for t in tarifas
            ])
        except Exception as e:
            print(f"❌ Error consultando tarifas: {e}")
            return jsonify([]), 500

    @app.route('/configurar_webhook', methods=['POST'])
    def configurar_webhook():
        # 1. Leemos el JSON que envía el script .bat
        data = request.get_json()
        url_tunel = data.get('url') if data else None
        
        if not url_tunel:
            return "Falta la URL del túnel en el cuerpo de la petición", 400
            
        import requests
        TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # 2. Tu lógica original (intacta)
        url_api = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={url_tunel}/telegram/webhook"
        try:
            respuesta = requests.get(url_api)
            print("[BOT] [TELEGRAM] Webhook configurado:", respuesta.json())
            return f"Webhook configurado con éxito a: {url_tunel}/telegram/webhook", 200
        except Exception as e:
            print("[ERROR] [TELEGRAM] No se pudo configurar el webhook:", e)
            return f"Error al configurar: {e}", 500

    from flask import redirect

    @app.route('/ir/<id_servicio>')
    def redirect_telegram(id_servicio):
        # Aquí puedes buscar el ID en tu BD si lo necesitas, o armar el start dinámico
        url_telegram = f"https://t.me/taxilospatriotastest_bot?start=srv-{id_servicio}"
        return redirect(url_telegram, code=302)

    @app.route('/s', methods=['GET'])
    @app.route('/s/<id_despacho>', methods=['GET'])
    def enlace_corto_parametro(id_despacho=None):
        # Si entra por ?id=... o por ruta limpia /s/19663
        if not id_despacho:
            id_despacho = request.args.get('id')
        
        return redirect(f"/monitoreo/{id_despacho}")
    from werkzeug.middleware.proxy_fix import ProxyFix
    
    # 🟢 1. IMPORTAR join_room aquí o arriba con las demás utilidades de socketio
    from flask_socketio import join_room

    # 🟢 2. REGISTRAR EL EVENTO DE SOCKET.IO PARA LA ROOM PRIVADA
    @socketio.on('unirse_room')
    def handle_unirse_room(data):
        despacho_id = data.get('despacho_id')
        if despacho_id:
            room = str(despacho_id)
            join_room(room)
            print(f"✅ Cliente unido exitosamente a la Room privada: {room}")
    @socketio.on('actualizar_gps_cliente')
    def handle_actualizar_gps_cliente(data):
        despacho_id = data.get('despacho_id')
        lat = data.get('lat')
        lon = data.get('lon')
        
        if despacho_id and lat and lon:
            room = str(despacho_id)
            # Reenviar la ubicación del cliente a todos los miembros de la sala (incluyendo al conductor si está conectado)
            socketio.emit('posicion_cliente', {
                'lat': lat,
                'lon': lon
            }, room=room)
            print(f"📍 Coordenada GPS del cliente recibida y retransmitida en la Room #{room}: ({lat}, {lon})")        
    app.wsgi_app = ProxyFix(
        app.wsgi_app, 
        x_for=1, 
        x_proto=1, 
        x_host=1, 
        x_prefix=1
    )

    return app

from werkzeug.middleware.proxy_fix import ProxyFix

if __name__ == "__main__":
    app = create_app()
    
    # Iniciar scheduler solo en el proceso hijo del reloader para evitar duplicidad
    if 'db' not in sys.argv and os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("[SCHEDULER] Tareas programadas iniciadas correctamente.")
        iniciar_scheduler(app, socketio)

    print("[SERVIDOR] Servidor iniciado con WebSockets (Eventlet)...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=app.config['DEBUG'])
   