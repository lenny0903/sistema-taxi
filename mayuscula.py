import unicodedata
from extensions import db
from models.clientes import Cliente

def normalizar_texto(texto):
    if not texto:
        return ""
    return unicodedata.normalize("NFC", texto)

def reparar_clientes():
    clientes = Cliente.query.all()
    for c in clientes:
        c.nombre = normalizar_texto(c.nombre)
        c.direccion = normalizar_texto(c.direccion)
        c.punto_referencia = normalizar_texto(c.punto_referencia)
    db.session.commit()
    print("✅ Campos reparados con acentos correctos en UTF-8")
