from app import create_app
from models.conductores import Conductor
from utils.time import hora_local

app = create_app()

with app.app_context():
    codigo = input("Ingresa el código del conductor (ej: B64): ").strip().upper()
    conductor = Conductor.query.filter_by(codigo=codigo).first()
    
    if not conductor:
        print(f"❌ Conductor {codigo} no encontrado")
    else:
        ahora = hora_local()
        
        # 🔧 NORMALIZAR: Quitar zona horaria para comparar con la BD (que es naive)
        ahora_naive = ahora.replace(tzinfo=None) if ahora.tzinfo else ahora
        
        print(f"\n{'='*60}")
        print(f"🔎 DIAGNÓSTICO DE GPS - {conductor.codigo} ({conductor.nombre})")
        print(f"{'='*60}")
        print(f"Hora del servidor: {ahora}")
        
        print(f"\n📍 COORDENADAS ACTUALES EN BD:")
        print(f"   Latitud: {conductor.latitud}")
        print(f"   Longitud: {conductor.longitud}")
        
        if conductor.latitud is None or conductor.longitud is None:
            print(f"   ⚠️ SIN COORDENADAS (nunca ha compartido ubicación)")
        else:
            print(f"   ✅ Coordenadas válidas")
        
        print(f"\n⏰ ÚLTIMA ACTUALIZACIÓN:")
        print(f"   Timestamp en BD: {conductor.ultima_actualizacion}")
        
        if conductor.ultima_actualizacion:
            # 🔧 Ya ambos son naive, ahora sí se pueden restar
            diff = ahora_naive - conductor.ultima_actualizacion
            minutos_sin_senal = int(diff.total_seconds() / 60)
            print(f"   Minutos transcurridos: {minutos_sin_senal}")
            
            tolerancia = conductor.tolerancia_dinamica_minutos or 5
            if minutos_sin_senal > tolerancia:
                print(f"   ⚠️ ESTADO: SIN SEÑAL (más de {tolerancia} min sin actualizar)")
            else:
                print(f"   ✅ ESTADO: ACTIVO (actualización reciente)")
        else:
            print(f"   ⚠️ NUNCA HA ACTUALIZADO")
        
        print(f"\n📋 CONFIGURACIÓN GPS:")
        print(f"   Opción elegida: {conductor.opcion_gps}")
        print(f"   Expiración programada: {conductor.expiracion_gps}")
        print(f"   Tolerancia dinámica: {conductor.tolerancia_dinamica_minutos} min")
        print(f"   Telegram ID: {conductor.telegram_id}")
        
        if conductor.latitud and conductor.longitud:
            print(f"\n🔗 ENLACE PARA VER EN MAPA:")
            print(f"   https://www.google.com/maps?q={conductor.latitud},{conductor.longitud}")
        
        print(f"{'='*60}\n")