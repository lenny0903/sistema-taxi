from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from yourapp.models import Usuario, db

@clientes_bp.route('/cambiar_password', methods=['PUT'])
def cambiar_password():
    data = request.get_json()
    usuario = data.get("usuario")
    actual = data.get("password_actual")
    nueva = data.get("password_nueva")

    if not usuario or not actual or not nueva:
        return jsonify({"error": "Datos incompletos"}), 400

    user = Usuario.query.filter_by(usuario=usuario).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Validar contraseña actual
    if not check_password_hash(user.password_hash, actual):
        return jsonify({"error": "Contraseña actual incorrecta"}), 401

    # Guardar nueva contraseña con hash
    user.password_hash = generate_password_hash(nueva, method="pbkdf2:sha256", salt_length=16)
    db.session.commit()

    return jsonify({"message": "Contraseña actualizada correctamente"}), 200
