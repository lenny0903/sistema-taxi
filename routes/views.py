from flask import Blueprint, render_template, request, redirect, session
from models.usuarios import Usuario
from models.despachos import Despacho
from werkzeug.security import check_password_hash

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
    return render_template("panel_operador.html", title="Panel Operador", despachos=despachos)

@views_bp.route("/panel_admin")
def panel_admin():
    despachos = Despacho.query.all()
    return render_template("panel_admin.html", title="Panel Administrador", despachos=despachos)
