from datetime import datetime
import pytz
from utils.telegram_helpers import enviar_ping_telegram

# Zona horaria de Caracas para comparar fechas correctamente
CARACAS_TZ = pytz.timezone('America/Caracas')

def evaluar_estado_flota_backend(db_conexion, token_bot):
    cursor = db_conexion.cursor()
    
    # Obtenemos los conductores activos que tienen un chat_id de Telegram registrado
    cursor.execute("""
        SELECT id, codigo, chat_id, ultima_actualizacion, tolerancia_dinamica_minutos, aviso_enviado 
        FROM conductores 
        WHERE estado IN ('activo', 'en curso') AND chat_id IS NOT NULL
    """)
    conductores = cursor.fetchall()
    
    ahora = datetime.now(CARACAS_TZ)
    
    for c in conductores:
        id_cond, codigo, chat_id, ultima_act_str, tolerancia, aviso_enviado = c
        
        if not ultima_act_str:
            continue
            
        # Parsear la última actualización de forma segura
        try:
            ultima_act = datetime.fromisoformat(ultima_act_str)
            if ultima_act.tzinfo is None:
                ultima_act = CARACAS_TZ.localize(ultima_act)
        except Exception:
            continue
            
        # Calcular minutos sin reportar
        diferencia_minutos = (ahora - ultima_act).total_seconds() / 60.0
        tol_min = tolerancia if tolerancia else 5
        
        # 1. ESCENARIO DE ALERTA: Superó la tolerancia y NO se le ha avisado automáticamente
        if diferencia_minutos > tol_min and aviso_enviado == 0:
            print(f"⚠️ Unidad {codigo} sin señal por {round(diferencia_minutos)}m. Enviando ping automático...")
            
            # Disparamos el ping a Telegram usando la función que guardaste
            exito = enviar_ping_telegram(chat_id, token_bot)
            
            if exito:
                # Marcamos la bandera en 1 para evitar más spam
                cursor.execute("UPDATE conductores SET aviso_enviado = 1 WHERE id = ?", (id_cond,))
                db_conexion.commit()
                
        # 2. ESCENARIO DE RECUPERACIÓN: El carro volvió a reportar a tiempo
        elif diferencia_minutos <= tol_min and aviso_enviado == 1:
            # Reseteamos la bandera a 0
            cursor.execute("UPDATE conductores SET aviso_enviado = 0 WHERE id = ?", (id_cond,))
            db_conexion.commit()