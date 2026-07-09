from flask import Blueprint, app, render_template, request, redirect, session
from models.matriz_tarifas import MatrizTarifa
from models.usuarios import Usuario
from models.despachos import Despacho
from werkzeug.security import check_password_hash
from extensions import db
from flask import Blueprint, render_template, request, redirect, session, jsonify
from models.conductores import Conductor

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
    
    tarifa = MatrizTarifa.query.get(id_tarifa)
    
    if tarifa:
        # 🛠️ SINCRONIZACIÓN TOTAL:
        # Mapeamos lo que viene del JS (data.get) al modelo de SQLAlchemy (tarifa.campo)
        tarifa.destino = data.get('destino') # <--- ¡Esta línea faltaba!
        tarifa.municipio = data.get('municipio') # <--- ¡Y esta también!
        tarifa.precio_cop = data.get('precio_cop')
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Registro completo actualizado"})
    
    return jsonify({"status": "error", "message": "No encontrada"}), 404

@views_bp.route("/control/<codigo>")
def pagina_control(codigo):
    # Buscamos al conductor por su código para verificar que existe
    conductor = Conductor.query.filter_by(codigo=codigo).first_or_404()
    return render_template("control_conductor.html", conductor=conductor)
@views_bp.route("/monitoreo")
def pagina_mapa():
    return render_template("monitoreo.html")

@views_bp.route("/conductores/ubicaciones_activas")
def obtener_ubicaciones_activas():
    db.session.expire_all() 
    
    conductores = Conductor.query.all()
    lista_conductores = []
    for c in conductores:
        # Enviamos todos los datos, incluso si no tienen lat/lon, 
        # para que el frontend pueda limpiar marcadores si el conductor se desconectó
        lista_conductores.append({
            "codigo": c.codigo,
            "estado": c.estado,
            "latitud": c.latitud,
            "longitud": c.longitud,
            "ultima_actualizacion": str(c.ultima_actualizacion),
            "id_conductor": c.id # Asegúrate de enviar esto para tu botón de iniciar turno
        })
    return jsonify(lista_conductores)