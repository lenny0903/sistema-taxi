# utils/time.py
from datetime import datetime
from zoneinfo import ZoneInfo

# 🔹 Zona horaria oficial de Caracas
TZ_CARACAS = ZoneInfo("America/Caracas")

def hora_local():
    """
    Devuelve la hora actual en Caracas (UTC-4),
    con zona horaria explícita para evitar desfases.
    """
    return datetime.now(TZ_CARACAS)
