import os
from datetime import datetime
from extensions import db, socketio
from models.clientes import Cliente
from models.lista_espera import ListaEspera
# Si manejas un modelo de reservas separado, puedes importarlo aquí también
# from models.reservas import Reserva 

# Estructura de sesiones en memoria para cada chat_id de WhatsApp
# Guardará el estado de la conversación y los datos parciales del servicio
sesiones_clientes = {}

def emitir_al_panel(evento, datos=None):
    try:
        socketio.emit(evento, datos, namespace='/')
        print(f"✅ Evento '{evento}' emitido con éxito al panel del operador.")
    except Exception as e:
        print(f"❌ Error al emitir evento por Socket.IO: {e}")

def procesar_logica_negocio(evento, enviar_func):
    chat_id = evento.get("chat_id")
    telefono = evento.get("telefono")
    tipo_msg = evento.get("tipo_msg")
    texto = evento.get("texto", "").strip()
    lat = evento.get("lat")
    lng = evento.get("lng")

    if not chat_id:
        return

    # Inicializar o recuperar sesión del cliente
    if chat_id not in sesiones_clientes:
        sesiones_clientes[chat_id] = {"estado": "INICIAL"}

    sesion = sesiones_clientes[chat_id]
    estado_actual = sesion["estado"]
    print(f"🤖 [BOT AVANZADO] Chat: {chat_id} | Estado: {estado_actual} | Texto: {texto}")

    # ==========================================
    # 1. ESTADO INICIAL / MENÚ PRINCIPAL
    # ==========================================
    if texto.lower() in ["hola", "menu", "empezar", "pedir taxi"] or estado_actual == "INICIAL":
        cliente = Cliente.query.filter_by(telefono=telefono).first()
        
        # Guardamos datos básicos del cliente en la sesión
        sesion["cliente_id"] = cliente.id_cliente if cliente else None
        sesion["nombre"] = cliente.nombre if cliente else None

        menu_mensaje = (
            "🚖 ¡Bienvenido a Taxis Táchira!\n\n"
            "Por favor, selecciona el **tipo de servicio** que necesitas respondiendo con el número:\n\n"
            "1️⃣ **Servicio Inmediato** (1 Vehículo)\n"
            "2️⃣ **Reserva Programada** (Para otra fecha u hora)\n"
            "3️⃣ **Caravana / Mismo Destino** (2 a 4 vehículos al mismo lugar)\n"
            "4️⃣ **Diferentes Destinos** (2 a 4 vehículos independientes)"
        )
        
        if not cliente:
            sesion["estado"] = "ESPERANDO_NOMBRE_INICIAL"
            enviar_func(chat_id, "¡Hola! Para comenzar, indícanos **tu nombre y apellido**:")
        else:
            sesion["estado"] = "ESPERANDO_SELECCION_MODALIDAD"
            enviar_func(chat_id, f"¡Hola de nuevo, {cliente.nombre}! {menu_mensaje}")
        return

    # ==========================================
    # 2. REGISTRO DE NOMBRE (Cliente Nuevo)
    # ==========================================
    if estado_actual == "ESPERANDO_NOMBRE_INICIAL":
        if len(texto) < 2:
            enviar_func(chat_id, "⚠️ Por favor, escribe un nombre válido.")
            return

        try:
            nuevo_cliente = Cliente(
                nombre=texto.title(),
                telefono=telefono,
                direccion="Registrado vía WhatsApp"
            )
            db.session.add(nuevo_cliente)
            db.session.commit()

            sesion["cliente_id"] = nuevo_cliente.id_cliente
            sesion["nombre"] = nuevo_cliente.nombre
            sesion["estado"] = "ESPERANDO_SELECCION_MODALIDAD"

            menu_mensaje = (
                f"¡Mucho gusto, {nuevo_cliente.nombre}!\n\n"
                "Selecciona el tipo de servicio:\n"
                "1️⃣ **Servicio Inmediato** (1 Vehículo)\n"
                "2️⃣ **Reserva Programada**\n"
                "3️⃣ **Caravana / Mismo Destino** (2-4 vehículos)\n"
                "4️⃣ **Diferentes Destinos** (2-4 vehículos)"
            )
            enviar_func(chat_id, menu_mensaje)
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creando cliente: {e}")
            enviar_func(chat_id, "Hubo un error al registrar tus datos. Escribe 'hola' para reiniciar.")
            sesion["estado"] = "INICIAL"
        return

    # ==========================================
    # 3. SELECCIÓN DE MODALIDAD (1, 2, 3 o 4)
    # ==========================================
    if estado_actual == "ESPERANDO_SELECCION_MODALIDAD":
        if texto not in ["1", "2", "3", "4"]:
            enviar_func(chat_id, "⚠️ Opción no válida. Por favor, responde con un número del 1 al 4.")
            return

        sesion["modalidad"] = texto
        cliente_id = sesion.get("cliente_id")
        
        # Consultar si el cliente ya tiene una dirección guardada en BD
        direccion_guardada = None
        if cliente_id:
            cliente_db = Cliente.query.get(cliente_id)
            if cliente_db and cliente_db.direccion and cliente_db.direccion != "Registrado vía WhatsApp":
                direccion_guardada = cliente_db.direccion

        # Si tiene dirección registrada, la usamos directamente como origen y saltamos al destino
        if direccion_guardada:
            sesion["origen"] = direccion_guardada
            
            if texto == "3":
                sesion["estado"] = "ESPERANDO_DESTINO_UNICO"
                enviar_func(chat_id, f"📍 Usaremos tu dirección registrada:\n*{direccion_guardada*\n\n¿Cuál es el **destino** para la caravana?")
            elif texto == "4":
                sesion["estado"] = "ESPERANDO_DESTINOS_MULTIPLES"
                enviar_func(chat_id, f"📍 Usaremos tu dirección registrada:\n*{direccion_guardada*\n\nEscribe los **destinos separados por comas** para cada vehículo:")
            else:
                sesion["estado"] = "ESPERANDO_DESTINO_UNICO"
                enviar_func(chat_id, f"📍 Usaremos tu dirección registrada:\n*{direccion_guardada*\n\n¿Cuál es el **destino** del servicio?")
        else:
            # Si no tiene dirección previa, se la pedimos con normalidad
            if texto == "2":
                sesion["estado"] = "ESPERANDO_RESERVA_FECHA_HORA"
                enviar_func(chat_id, "📅 Indica la fecha y hora de la reserva (Ej: *25/10/2026 a las 03:30 PM*):")
            elif texto in ["3", "4"]:
                sesion["estado"] = "ESPERANDO_CANTIDAD_AUTOS" if texto=="3" else "ESPERANDO_CANTIDAD_AUTOS_DIF"
                enviar_func(chat_id, "¿Cuántos vehículos necesitas? (2, 3 o 4):")
            else:
                sesion["estado"] = "ESPERANDO_ORIGEN"
                enviar_func(chat_id, "📍 Por favor, indícanos tu **dirección de origen** o comparte tu ubicación GPS:")
        return
    # ==========================================
    # 4. FLUJO DE RESERVA PROGRAMADA (Modalidad 2)
    # ==========================================
    if estado_actual == "ESPERANDO_RESERVA_FECHA_HORA":
        sesion["reserva_fyh"] = texto
        sesion["estado"] = "ESPERANDO_ORIGEN"
        enviar_func(chat_id, "Perfecto. Ahora indícanos la **dirección de origen** (recogida):")
        return

    # ==========================================
    # 5. FLUJO DE CARAVANA O DIFERENTES (Modalidades 3 y 4)
    # ==========================================
    if estado_actual in ["ESPERANDO_CANTIDAD_AUTOS_MISMO", "ESPERANDO_CANTIDAD_AUTOS_DIF"]:
        if texto not in ["2", "3", "4"]:
            enviar_func(chat_id, "⚠️ Por favor, ingresa un número válido entre 2 y 4.")
            return
        
        sesion["cantidad_vehiculos"] = int(texto)
        sesion["estado"] = "ESPERANDO_ORIGEN"
        enviar_func(chat_id, f"Entendido, {texto} vehículos. Ahora, indícanos la **dirección de origen**:")
        return

    # ==========================================
    # 6. CAPTURA DE ORIGEN (Común para todos)
    # ==========================================
    if estado_actual == "ESPERANDO_ORIGEN":
        origen_texto = f"Ubicación GPS (Lat: {lat}, Lng: {lng})" if (tipo_msg == "locationMessage" or (lat and lng)) else texto
        if not origen_texto:
            enviar_func(chat_id, "⚠️ Por favor, escribe la dirección de recogida o comparte tu ubicación GPS.")
            return

        sesion["origen"] = origen_texto
        
        # Si es caravana (modalidad 3), van al mismo destino. Preguntamos destino único.
        if sesion.get("modalidad") == "3":
            sesion["estado"] = "ESPERANDO_DESTINO_UNICO"
            enviar_func(chat_id, "📍 ¿Cuál es el **destino** para toda la caravana?")
        elif sesion.get("modalidad") == "4":
            sesion["estado"] = "ESPERANDO_DESTINOS_MULTIPLES"
            enviar_func(chat_id, "📍 Por favor, escribe los **destinos separados por comas** para cada uno de los vehículos:")
        else:
            sesion["estado"] = "ESPERANDO_DESTINO_UNICO"
            enviar_func(chat_id, "📍 ¿Cuál es el **destino** del servicio?")
        return

    # ==========================================
    # 7. CAPTURA DE DESTINO E INSERCIÓN FINAL
    # ==========================================
    if estado_actual in ["ESPERANDO_DESTINO_UNICO", "ESPERANDO_DESTINOS_MULTIPLES"]:
        if not texto:
            enviar_func(chat_id, "⚠️ Por favor, ingresa el destino correspondiente.")
            return

        sesion["destino"] = texto
        
        # Extraemos datos acumulados
        modalidad = sesion.get("modalidad")
        cliente_id = sesion.get("cliente_id")
        nombre_cliente = sesion.get("nombre")
        origen = sesion.get("origen")
        destino = sesion.get("destino")
        cantidad = sesion.get("cantidad_vehiculos", 1)
        reserva_fyh = sesion.get("reserva_fyh", "Inmediato")

        try:
            # 🚀 INSERCIÓN AUTOMÁTICA EN LA COLA O RESERVA SEGÚN MODALIDAD
            tipo_despacho_str = "Inmediato (1 Unidad)"
            if modalidad == "2":
                tipo_despacho_str = f"Reserva Programada ({reserva_fyh})"
            elif modalidad == "3":
                tipo_despacho_str = f"Caravana - {cantidad} Vehículos Mismo Destino"
            elif modalidad == "4":
                tipo_despacho_str = f"Diferentes Destinos - {cantidad} Vehículos"

            nueva_solicitud = ListaEspera(
                cliente_id=cliente_id,
                origen=origen,
                destino=f"[{tipo_despacho_str}] Destino: {destino}",
                estado="pendiente"
            )
            db.session.add(nueva_solicitud)
            db.session.commit()

            # Emitir evento por Socket.IO al panel del operador en tiempo real
            emitir_al_panel('nuevo_cliente_cola', {
                'id': nueva_solicitud.id if hasattr(nueva_solicitud, 'id') else 1,
                'telefono': telefono,
                'cliente': nombre_cliente,
                'origen': origen,
                'destino': f"[{tipo_despacho_str}] {destino}",
                'estado': 'pendiente'
            })

            enviar_func(chat_id, f"✅ ¡Solicitud registrada con éxito!\n\n📋 **Tipo:** {tipo_despacho_str}\n- **Origen:** {origen}\n- **Destino:** {destino}\n\nUn operador procesará tu requerimiento en breve. ¡Gracias! 🚖")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al registrar servicio avanzado: {e}")
            enviar_func(chat_id, "⚠️ Ocurrió un error al procesar tu solicitud. Escribe 'hola' para intentar de nuevo.")

        # Limpiar sesión
        sesiones_clientes[chat_id] = {"estado": "INICIAL"}
        return