from flask_jwt_extended import JWTManager   # <-- importa JWTManager
from flask import Flask, render_template
from flask_migrate import Migrate
from extensions import db
from routes.views import views_bp
from flask import send_from_directory
from models.turnos import Turno
from flask_sqlalchemy import SQLAlchemy
import config


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    print("📂 Base conectada:", app.config['SQLALCHEMY_DATABASE_URI'])
    migrate = Migrate(app, db)
     # 🔑 Clave secreta para sesiones
    app.secret_key = "clave_super_secreta_unica"  
    # Puedes usar cualquier string largo y único
    db.init_app(app)
    jwt = JWTManager(app)
    with app.app_context():
        import models
        from models.lista_espera import ListaEspera
        db.create_all()

    # Importar y registrar blueprints
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
    app.register_blueprint(init_bp)

    #print("Registrando blueprints...")

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

    print(app.url_map)

           
    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/index.html")
    def index_html():
       return render_template("index.html")
    @app.route("/panel.html")
    def panel_html():
        return render_template("dashboard.html")
    return app

    
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
