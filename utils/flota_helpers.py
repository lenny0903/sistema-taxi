from datetime import datetime
import pytz
from sqlalchemy import text
from utils.telegram_helpers import enviar_ping_telegram

# Zona horaria de Caracas para comparar fechas correctamente
CARACAS_TZ = pytz.timezone('America/Caracas')

def evaluar_estado_flota_backend(db_conexion, token_bot):
    # 🟢 Consulta exacta basada en los campos reales de tu modelo Conductor
    query = text("""
        SELECT id_conductor, codigo, telegram_id, ultima_actualizacion, tolerancia_dinamica_minutos, aviso_enviado 
        FROM conductores 
        WHERE estado IN ('activo', 'en curso') AND telegram_id IS NOT NULL
    """)
    
    resultados = db_conexion.execute(query).fetchall()
    ahora = datetime.now(CARACAS_TZ)
    
    for row in resultados:
        id_cond, codigo, telegram_id, ultima_act_str, tolerancia, aviso_enviado = row
        
        if not ultima_act_str:
            continue
            
        try:
            # Manejo seguro si la fecha viene como texto de la BD
            if isinstance(ultima_act_str, str):
                ultima_act_clean = ultima_act_str.split('.')[0].replace('T', ' ')
                ultima_act = datetime.strptime(ultima_act_clean, "%Y-%m-%d %H:%M:%S")
            else:
                ultima_act = ultima_act_str

            if ultima_act.tzinfo is None:
                ultima_act = CARACAS_TZ.localize(ultima_act)
        except Exception:
            continue
            
        diferencia_minutos = (ahora - ultima_act).total_seconds() / 60.0
        tol_min = tolerancia if tolerancia else 5
        
        # 1. ESCENARIO DE ALERTA: Superó la tolerancia y NO se le ha avisado automáticamente
        if diferencia_minutos > tol_min and aviso_enviado == 0:
            print(f"⚠️ Unidad {codigo} sin señal por {round(diferencia_minutos)}m. Enviando ping automático...")
            
            exito = enviar_ping_telegram(telegram_id, token_bot)
            
            if exito:
                update_query = text("UPDATE conductores SET aviso_enviado = 1 WHERE id_conductor = :id_cond")
                db_conexion.execute(update_query, {"id_cond": id_cond})
                db_conexion.commit()
                
        # 2. ESCENARIO DE RECUPERACIÓN: El carro volvió a reportar a tiempo
        elif diferencia_minutos <= tol_min and aviso_enviado == 1:
            update_query = text("UPDATE conductores SET aviso_enviado = 0 WHERE id_conductor = :id_cond")
            db_conexion.execute(update_query, {"id_cond": id_cond})
            db_conexion.commit()