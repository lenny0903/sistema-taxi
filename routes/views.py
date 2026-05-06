from flask import Blueprint, app, render_template, request, redirect, session
from models.matriz_tarifas import MatrizTarifa
from models.usuarios import Usuario
from models.despachos import Despacho
from werkzeug.security import check_password_hash
from extensions import db
from flask import Blueprint, render_template, request, redirect, session, jsonify


views_bp = Blueprint("views", __name__)

# 🔒 Elimina esta ruta para no pisar index.html
# @views_bp.route("/")
# def home():
#     return redirect("/login")

@views_bp.route("/login_alt")
def login_page_alt():
    return render_template("login.html", title="Login")

@views_bp.route("/auth/login_html", methods=["POST"])
def login_html():
    username = request.form["username"]
    password = request.form["password"]
    usuario = Usuario.query.filter_by(username=username).first()

    if usuario and check_password_hash(usuario.password_hash, password):
        session["rol_id"] = usuario.rol_id
        if usuario.rol_id == 1:
            return redirect("/panel_admin")
        else:
            return redirect("/panel_operador")
    return "Credenciales inválidas", 401

@views_bp.route("/panel_operador")
def panel_operador():
    despachos = Despacho.query.all()
    # AGREGA ESTO:
    tarifas = MatrizTarifa.query.all()
    destinos_lista = [{"destino": t.destino, "precio_cop": t.precio_cop, "municipio": t.municipio} for t in tarifas]
    
    return render_template("panel_operador.html", title="Panel Operador", despachos=despachos, destinos=destinos_lista)

@views_bp.route("/panel_admin")
def panel_admin():
    despachos = Despacho.query.all()
    destinos_query = MatrizTarifa.query.all()
    
    # Esto saldrá en tu terminal de Linux Mint
    print(f"DEBUG: Se encontraron {len(destinos_query)} registros en la matriz.")
    
    return render_template("panel_admin.html", 
                           title="Panel Administrador", 
                           despachos=despachos, 
                           destinos=destinos_query)

@views_bp.route("/actualizar_tarifa", methods=["POST"])
def actualizar_tarifa():
    data = request.get_json()
    id_tarifa = data.get('id')
    nuevo_precio = data.get('precio_cop')
    
    tarifa = MatrizTarifa.query.get(id_tarifa)
    if tarifa:
        tarifa.precio_cop = nuevo_precio
        db.session.commit()
        return jsonify({"status": "success", "message": "Tarifa actualizada"})
    return jsonify({"status": "error", "message": "No encontrada"}), 404
