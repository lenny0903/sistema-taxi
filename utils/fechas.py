# utils/fechas.py
from datetime import datetime
import pytz

# Zona horaria de Caracas
TZ_CARACAS = pytz.timezone("America/Caracas")

def hora_local():
    """
    Devuelve la fecha y hora actual en Caracas con formato datetime.
    """
    return datetime.now(TZ_CARACAS)
