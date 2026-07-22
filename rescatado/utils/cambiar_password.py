from werkzeug.security import generate_password_hash, check_password_hash
from yourapp.models import Usuario, db

def cambiar_password(usuario: str, actual: str, nueva: str) -> dict:
    user = Usuario.query.filter_by(usuario=usuario).first()
    if not user:
        return {"error": "Usuario no encontrado"}, 404

    if not check_password_hash(user.password_hash, actual):
        return {"error": "Contraseña actual incorrecta"}, 401

    user.password_hash = generate_password_hash(nueva, method="pbkdf2:sha256", salt_length=16)
    db.session.commit()
    return {"message": "Contraseña actualizada correctamente"}, 200

