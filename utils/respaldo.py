from flask import Blueprint, jsonify, send_file
from datetime import datetime
from flask import current_app
import os

respaldo_bp = Blueprint("respaldo", __name__)

@respaldo_bp.route("/respaldar", methods=["GET"])
def respaldar():
    try:
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{fecha}.sqlite"

        # Obtener ruta real desde la configuración
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace("sqlite:///", "")  # quita el prefijo

        print("📂 Respaldo leyendo desde:", db_path)

        with open(db_path, "rb") as original, open(backup_file, "wb") as copia:
            copia.write(original.read())

        return send_file(backup_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Error al generar respaldo: {str(e)}"}), 500

