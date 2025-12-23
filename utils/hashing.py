from werkzeug.security import generate_password_hash, check_password_hash

def hash_clave(clave):
    return generate_password_hash(clave)

def verificar_clave(clave, hash_guardado):
    return check_password_hash(hash_guardado, clave)
