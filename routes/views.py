from flask import Blueprint, render_template, request, redirect, session, jsonify
from datetime import datetime, timedelta
from sqlalchemy import text
from werkzeug.security import check_password_hash
from extensions import db

from models.matriz_tarifas import MatrizTarifa
from models.turnos import Turno
from models.usuarios import Usuario
from models.despachos import Despacho  # <--- Importación limpia y directa en singular
from models.conductores import Conductor

views_bp = Blueprint("views", __name__)
views_bp = Blueprint("views", __name__)

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
    tarifas = MatrizTarifa.query.all()
    destinos_lista = [{"destino": t.destino, "precio_cop": t.precio_cop, "municipio": t.municipio} for t in tarifas]
    
    return render_template("panel_operador.html", title="Panel Operador", despachos=despachos, destinos=destinos_lista)

@views_bp.route("/panel_admin")
def panel_admin():
    despachos = Despacho.query.all()
    destinos_query = MatrizTarifa.query.all()
    
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
        tarifa.destino = data.get('destino')
        tarifa.municipio = data.get('municipio')
        tarifa.precio_cop = data.get('precio_cop')
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Registro completo actualizado"})
    
    return jsonify({"status": "error", "message": "No encontrada"}), 404

@views_bp.route("/control/<codigo>")
def pagina_control(codigo):
    conductor = Conductor.query.filter_by(codigo=codigo).first_or_404()
    return render_template("control_conductor.html", conductor=conductor)

@views_bp.route("/monitoreo")
def pagina_mapa():
    return render_template("monitoreo.html")

from datetime import datetime
from sqlalchemy import text
from flask import jsonify

@views_bp.route("/conductores/ubicaciones_activas")
def obtener_ubicaciones_activas():
    sql = text("""
        SELECT c.codigo, c.estado, c.latitud, c.longitud, c.id_conductor, 
               c.ultima_actualizacion, c.horizontal_accuracy,
               c.opcion_gps, c.expiracion_gps, t.fecha_inicio
        FROM conductores c
        LEFT JOIN turnos t ON c.id_conductor = t.conductor_id AND t.estado = 'activo'
        WHERE c.estado IN ('esperando', 'disponible', 'activo', 'solicitando_cierre')
    """)
    resultados = db.session.execute(sql).fetchall()
    
    ahora = datetime.now()
    lista_conductores = []
    
    for row in resultados:
        expiracion = row.expiracion_gps
        opcion_raw = str(row.opcion_gps or '').strip().lower()

        # Parsear expiracion_gps
        if isinstance(expiracion, str):
            try:
                expiracion = datetime.fromisoformat(expiracion.replace('Z', ''))
            except ValueError:
                expiracion = None

        # Si no hay fecha de expiración, la calculamos a partir del inicio del turno
        if not expiracion:
            inicio = row.fecha_inicio or row.ultima_actualizacion
            if isinstance(inicio, str):
                try:
                    inicio = datetime.fromisoformat(inicio.replace('Z', ''))
                except ValueError:
                    inicio = None
            
            if inicio:
                if "15" in opcion_raw:
                    expiracion = inicio + timedelta(minutes=15)
                elif "1" in opcion_raw:  # Captura "1", "1h", "1 hora"
                    expiracion = inicio + timedelta(hours=1)
                elif "8" in opcion_raw or opcion_raw == "":  # Captura "8", "8h", "8 horas" o por defecto la jornada estándar de 8h
                    expiracion = inicio + timedelta(hours=8)

        # Determinar si es "En vivo" sin límite de tiempo
        es_en_vivo = ("hasta" in opcion_raw) or ("desactive" in opcion_raw) or (opcion_raw == "en vivo")

        if es_en_vivo:
            opcion_label = "En vivo"
            tiempo_restante = "Jornada Activa"
        elif expiracion:
            opcion_label = "Tiempo límite"
            if expiracion > ahora:
                diferencia = expiracion - ahora
                horas, resto = divmod(diferencia.seconds, 3600)
                minutos, _ = divmod(resto, 60)
                
                if horas > 0:
                    tiempo_restante = f"{horas}h {minutos}m restantes"
                else:
                    tiempo_restante = f"{minutos}m restantes"
            else:
                tiempo_restante = "Expirado"
        else:
            opcion_label = "En vivo"
            tiempo_restante = "Jornada Activa"

        lista_conductores.append({
            "codigo": row.codigo,
            "estado": row.estado,
            "latitud": row.latitud,
            "longitud": row.longitud,
            "modo": "gps",
            "horizontal_accuracy": row.horizontal_accuracy,
            "ultima_actualizacion": row.ultima_actualizacion.isoformat() if hasattr(row.ultima_actualizacion, 'isoformat') else str(row.ultima_actualizacion or ''),
            "id_conductor": row.id_conductor,
            "opcion_gps": opcion_label,
            "tiempo_restante": tiempo_restante
        })
        
    return jsonify(lista_conductores)

@views_bp.route("/recibir_gps", methods=["POST"])
def recibir_gps():
    datos = request.json
    if not datos:
        return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

    codigo = datos.get("codigo")
    lat = datos.get("latitud")
    lon = datos.get("longitud")
    
    if not codigo or lat is None or lon is None:
        return jsonify({"status": "error", "message": "Faltan parámetros"}), 400

    try:
        ahora = datetime.now()
        # 👈 Se actualiza la expiración para que no quede atascada en el pasado
        expiracion = ahora + timedelta(hours=8)

        sql = text("""
            UPDATE conductores 
            SET latitud = :lat, 
                longitud = :lon, 
                estado = 'activo',
                ultima_actualizacion = :ahora,
                expiracion_gps = :expiracion
            WHERE codigo = :codigo
        """)
        db.session.execute(sql, {
            "lat": lat, 
            "lon": lon, 
            "codigo": codigo,
            "ahora": ahora,
            "expiracion": expiracion
        })
        db.session.commit()
        
        return jsonify({"status": "ok", "message": "Ubicación actualizada"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@views_bp.route("/conductor/<codigo>")
def vista_conductor(codigo):
    return render_template("conductor.html", codigo=codigo)