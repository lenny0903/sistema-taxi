// ==================== Bloque 1: Flujo rápido (alta demanda) ====================
let memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} };
// * 🟢 Función Global para llenar el selectConductorUnico
// * Mapea resilientemente los campos del backend (codigo/numero_control, id_conductor, nombre)
// */
window.llenarSelectConductoresUnico = function(conductoresEnTurno) {
    const selectCond = document.getElementById("selectConductorUnico");
    
    if (!selectCond) {
        console.warn("⚠️ No se encontró el elemento <select id='selectConductorUnico'>.");
        return;
    }

    // Limpiar opciones previas manteniendo la opción por defecto para cola
    selectCond.innerHTML = '<option value="">-- Sin Conductor (Enviar a Cola) --</option>';

    if (!Array.isArray(conductoresEnTurno) || conductoresEnTurno.length === 0) {
        console.warn("⚠️ Arreglo de conductores en turno vacío.");
        return;
    }

    let contador = 0;
    conductoresEnTurno.forEach(item => {
        // Soporte para estructura anidada { conductor: {...}, auto: {...} } o plana
        const c = item.conductor || item;
        const a = item.auto || item;

        // Validar que el turno o conductor esté libre/disponible
        const estadoTurno = item.estado || c.estado || "disponible";
        
        if (estadoTurno === "disponible" || estadoTurno === "en_turno" || estadoTurno === "activo") {
            const option = document.createElement("option");
            
            const idConductor = c.id_conductor || c.id || item.id_conductor;
            const idAuto = a.id_auto || item.id_auto || idConductor;
            const nroControl = c.codigo || c.numero_control || c.nro_control || "B1";
            const nombre = c.nombre || c.nombre_conductor || "Conductor";

            if (idConductor) {
                option.value = idConductor;
                option.dataset.autoId = idAuto;
                option.textContent = `[${nroControl}] ${nombre}`;

                selectCond.appendChild(option);
                contador++;
            }
        }
    });

    console.log(`✅ Select Express poblado exitosamente con ${contador} conductor(es) en turno.`);
};
/**
 * 📡 Consulta autosuficiente para cargar el select express al iniciar o cambiar cliente
 */
/**
 * 📡 Consulta autosuficiente para cargar únicamente los conductores EN TURNO
 */
async function refrescarSelectConductorUnico() {
    try {
        const data = await apiFetch('/conductores/en_turno_disponibles');
        console.log("📡 [EXPRESS] Conductores en turno recibidos:", data);

        let listaData = data;
        if (data && typeof data.json === 'function') {
            listaData = await data.json();
        }

        if (Array.isArray(listaData)) {
            window.llenarSelectConductoresUnico(listaData);
        }
    } catch (err) {
        console.error("❌ [EXPRESS] Error al refrescar selectConductorUnico en turno:", err);
    }
}
window.refrescarSelectConductorUnico = refrescarSelectConductorUnico;
/**
 * 🚀 Función centralizada reutilizable para procesar Despachos Directos
 * Maneja validación de afinidad, API POST /despachos/ y creación del banner flotante.
 */
async function ejecutarDespachoDirecto({ clienteId, conductorId, autoId, origen, destino, tarifa, idCola = null, optionCondText = "" }) {
    if (!origen || !tarifa) {
        mostrarToast("⚠️ El origen y la tarifa son obligatorios", "error");
        return false;
    }

    if (!clienteId || !conductorId) {
        mostrarToast("⚠️ Datos de cliente o conductor incompletos", "error");
        return false;
    }

    try {
        // 🚨 1. Validar exclusión mutua / afinidad
        const checkAfinidad = await apiFetch("/incidencias/validar_afinidad", {
            method: "POST",
            body: JSON.stringify({
                cliente_id: parseInt(clienteId),
                conductor_id: parseInt(conductorId)
            })
        });

        if (checkAfinidad && checkAfinidad.permitido === false) {
            mostrarToast(checkAfinidad.mensaje, "error");
            return false; // Bloqueado por incompatibilidad
        }

        // 🚀 2. Enviar payload a la API
        const payload = {
            cliente_id: parseInt(clienteId),
            conductor_id: parseInt(conductorId),
            auto_id: parseInt(autoId || conductorId),
            origen_despacho: origen,
            destino_despacho: destino,
            tarifa: parseFloat(tarifa),
            estado_despacho: "en curso"
        };

        if (idCola) {
            payload.id_notificacion = parseInt(idCola);
        }

        const result = await apiFetch("/despachos/", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (result && !result.error) {
            mostrarToast(`✅ Despacho creado con éxito`, "success");

            // 📲 3. GENERAR BANNER FLOTANTE (WHATSAPP & COPYS)
            const inputNombre = document.getElementById("desNombre") || document.getElementById("modalNombreCliente");
            const inputTelefono = document.getElementById("desTelefono") || document.getElementById("modalTelefonoCliente");
            
            const nombreCliente = window.nombreClienteGlobal || (inputNombre ? inputNombre.value.trim() : "Cliente");
            const telefonoCliente = result.cliente_telefono || (inputTelefono ? inputTelefono.value.trim() : "") || "";

            let telClienteLimpiado = telefonoCliente.replace(/\D/g, '');
            if (telClienteLimpiado.startsWith('0') && telClienteLimpiado.length === 11) {
                telClienteLimpiado = '58' + telClienteLimpiado.substring(1);
            }

            const matchControl = optionCondText.match(/(B\d+)/i);
            const nroControl = matchControl ? matchControl[1].trim().toUpperCase() : "B1";
            const rutaFlayerLocal = `/static/flayers/${nroControl}.png`;
            const nombreCond = optionCondText.includes(' - ') ? optionCondText.split(' - ')[1] : optionCondText || "Conductor";
            
            const botTelegram = "@Taxilospatriotastest_bot";
            
            const msgCliente = 
                `¡Hola! 🚖 Su unidad va en camino.\n\n` +
                `🚗 *UNIDAD ASIGNADA: #${nroControl}*\n` +
                `• Conductor: *${nombreCond}*\n` +
                `• Vehículo: *Vehículo*\n` +
                `• Placa: **\n\n` +
                `📍 Para ver el mapa y rastreo en tiempo real, abra su Telegram, busque el bot *${botTelegram}* y envíe la palabra: *UBI*`;

            const nroControlConductor = nroControl !== "B1" ? nroControl : optionCondText;

            const msgConductor = 
                `🚖 *NUEVO DESPACHO ASIGNADO* (#${result.id_despacho})\n\n` +
                `📍 *Origen:* ${origen}\n` +
                `🏁 *Destino:* ${destino}\n` +
                `👤 *Cliente:* ${nombreCliente}\n` +
                `📞 *Teléfono:* ${telefonoCliente}\n\n` +
                `¡Buen viaje! 🚀`;

            // Crear el Banner Flotante
            const bannerAnterior = document.getElementById('bannerDespachoFlotante');
            if (bannerAnterior) bannerAnterior.remove();

            const bannerDiv = document.createElement('div');
            bannerDiv.id = 'bannerDespachoFlotante';
            bannerDiv.style.cssText = "position: fixed; bottom: 20px; right: 20px; background: #222; color: #fff; padding: 12px 18px; border-radius: 8px; z-index: 10000; box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: flex; align-items: center; gap: 12px; font-family: sans-serif;";
            
            bannerDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <img src="${rutaFlayerLocal}" alt="Flayer" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #25d366; background: #444;" onerror="this.src='https://via.placeholder.com/40?text=🚗'">
                    <span style="font-weight: bold;">Despacho #${result.id_despacho}</span>
                </div>
                <button id="btnCli" style="background: #25d366; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" title="Copia la imagen del flayer">
                    🖼️ ${nombreCliente} - ${window.telefonoClienteGlobal || telefonoCliente} (Copiar Flayer) 📲
                </button>
                <button id="btnTextoCli" style="background: #0088cc; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" title="Copia el mensaje de texto para el cliente">
                    💬 ${nombreCliente} - ${window.telefonoClienteGlobal || telefonoCliente} (Copiar Texto) 📋
                </button>
                <button id="btnCond" style="background: #128c7e; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" title="Copia mensaje para el conductor">
                    🚗 ${nroControlConductor} (Copiar Conductor) 📋
                </button>
                <button id="btnCerrarBanner" style="background: #555; color: white; border: none; padding: 6px 8px; border-radius: 4px; cursor: pointer;" title="Cerrar">✕</button>
            `;
            
            document.body.appendChild(bannerDiv);

            // Listeners de los botones del banner
            bannerDiv.querySelector('#btnCli').addEventListener('click', async () => {
                try {
                    const response = await fetch(rutaFlayerLocal);
                    if (!response.ok) throw new Error("No se encontró la imagen");
                    const blob = await response.blob();
                    await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
                    mostrarToast("🖼️ Flayer copiado. Pégalo en WhatsApp con Ctrl+V", "success");
                } catch (err) {
                    mostrarToast("⚠️ No se pudo cargar la imagen del flayer", "error");
                }
            });

            bannerDiv.querySelector('#btnTextoCli').addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(msgCliente);
                    mostrarToast("📋 Mensaje para el cliente copiado al portapapeles", "success");
                } catch (err) {
                    mostrarToast("⚠️ No se pudo copiar el texto", "error");
                }
            });

            bannerDiv.querySelector('#btnCond').addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(msgConductor);
                    mostrarToast("📋 Mensaje de conductor copiado", "success");
                } catch (err) {
                    mostrarToast("⚠️ No se pudo copiar", "error");
                }
            });

            bannerDiv.querySelector('#btnCerrarBanner').addEventListener('click', () => bannerDiv.remove());

            // 🔄 4. Refresco en paralelo del sistema
            Promise.all([
                cargarColaClientes(),
                typeof refrescarSelectConductorUnico === 'function' ? refrescarSelectConductorUnico() : Promise.resolve(),
                typeof refrescarConductoresDisponibles === 'function' ? refrescarConductoresDisponibles() : Promise.resolve()
            ]);

            return true;
        } else {
            mostrarToast("❌ Error: " + (result.error || "No se pudo crear el despacho"), "error");
            return false;
        }
    } catch (err) {
        console.error("❌ Error en Despacho:", err);
        mostrarToast("❌ Error de conexión o del servidor", "error");
        return false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const formDespacho = document.getElementById("formDespacho");
    const telefonoInput = document.getElementById("desTelefono");
    const btnEnviar = document.getElementById("btnEnviarDespacho");

    if (btnEnviar) btnEnviar.disabled = true;

    // Carga inicial del select express de conductores
    refrescarSelectConductorUnico();

    let clienteListoParaEnviar = null; 

    telefonoInput?.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            const telActual = telefonoInput.value.trim();
            if (telActual === "") {
                console.log("🚫 Enter ignorado: Campo vacío.");
                event.preventDefault();
                event.stopImmediatePropagation();
                return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();

            if (!telefonoInput.checkValidity()) {
                mostrarToast("⚠️ " + telefonoInput.validationMessage, "error");
                telefonoInput.reportValidity();
                return; 
            }

            const inputNom = document.getElementById("desNombre");
            const inputOri = document.getElementById("desOrigen");
            const inputDes = document.getElementById("desDestino");
            const btnEnv = document.getElementById("btnEnviarDespacho");

            if (clienteListoParaEnviar === telActual && inputNom && inputNom.value.trim() !== "") {
                console.log("🚀 SEMÁFORO VERDE: Enviando despacho...");
                if (btnEnv) {
                    btnEnv.disabled = false;
                    btnEnv.click();
                }
                clienteListoParaEnviar = null; 
                return;
            }

            console.log("⌨️ SEMÁFORO ROJO: Preparando nueva validación...");
            clienteListoParaEnviar = null; 

            if (inputNom) inputNom.value = "Buscando..."; 
            if (inputOri) inputOri.value = "Buscando..."; 
            if (inputDes) inputDes.value = ""; 

            // Forzamos actualización de conductores al buscar cliente
            refrescarSelectConductorUnico();

            const resultado = await validarClienteExpreso();
            
            if (resultado && resultado.valido === true && resultado.cliente) {
                const c = resultado.cliente;
                
                if (inputNom) {
                    inputNom.value = c.nombre || "";
                    inputNom.readOnly = true;
                    inputNom.style.backgroundColor = "#f3f4f6"; 
                }
                if (inputOri) {
                    inputOri.value = c.direccion || "";
                    inputOri.readOnly = false;
                    inputOri.style.backgroundColor = "#f3f4f6";
                }

                const btnMod = document.getElementById("btnModificarCliente"); 
                if (btnMod) {
                    btnMod.disabled = false;
                    btnMod.style.opacity = "1";
                    btnMod.onclick = () => {
                        if (!c.id_cliente) c.id_cliente = c.cliente_id || c.id;
                        abrirModalCliente(telActual, c); 
                    };
                }
               
                if (inputDes) {
                    inputDes.disabled = false;
                    inputDes.readOnly = false;
                    inputDes.style.backgroundColor = "#ffffff";
                    inputDes.value = ""; 
                    inputDes.focus();
                }
                clienteListoParaEnviar = telActual; 
                if (btnEnv) btnEnv.disabled = false;
                
                console.log("✅ Validación completa. Siguiente Enter enviará.");
                const idParaIncidencia = c.id_cliente || c.cliente_id || c.id;
                if (idParaIncidencia) {
                    try {
                       const token = localStorage.getItem("token");
                        const resInc = await fetch(`/incidencias/verificar_cliente/${idParaIncidencia}`, {
                            method: "GET",
                            headers: { 
                                "Content-Type": "application/json",
                                "Authorization": `Bearer ${token}` 
                            }
                        });

                       if (resInc.ok) {
                            const check = await resInc.json();
                            console.log("🛑 Datos recibidos (Dinámicos):", check);

                            if (check.tiene_veto_general === true) {
                                const msgVeto = check.mensaje_veto || "Veto administrativo";
                                crearToastEmergencia(`🚫 ${msgVeto}`);
                            } 
                            else if (check.tiene_exclusiones === true && check.origen_reporte === "CLIENTE") {
                                const catReal = check.categoria || "INCIDENCIA"; 
                                const descReal = check.descripcion || "Sin descripción";
                                crearToastEmergencia(`⚠️ Alerta Cliente - ${catReal}: ${descReal}`);
                            }
                        }
                    } catch (err) {
                        console.error("❌ Error en incidencias:", err);
                    }
                }

            } else {
                console.log("🆕 Cliente no encontrado.");
                
                if (typeof mostrarToast === 'function') {
                    mostrarToast("✨ Cliente nuevo. Ingresa el nombre y origen.", "info");
                }

                const inputNom = document.getElementById("desNombre");
                const inputOri = document.getElementById("desOrigen");
                const inputDes = document.getElementById("desDestino");
                const btnEnv = document.getElementById("btnEnviarDespacho");

                if (inputNom) {
                    inputNom.disabled = false;     
                    inputNom.readOnly = false;     
                    inputNom.value = "";
                    inputNom.style.backgroundColor = "#ffffff";
                }

                if (inputOri) {
                    inputOri.disabled = false;     
                    inputOri.readOnly = false;
                    inputOri.value = "";
                    inputOri.style.backgroundColor = "#ffffff";
                }

                if (inputDes) {
                    inputDes.disabled = false;
                    inputDes.readOnly = false;
                }

                window.clienteIdActual = null;
                clienteListoParaEnviar = telActual; 
                if (btnEnv) btnEnv.disabled = false;

                // ⚡ Único salto de foco inicial hacia el nombre
                telefonoInput.blur();
                
                setTimeout(() => {
                    if (inputNom) {
                        inputNom.focus();
                        inputNom.select();
                    }
                }, 50);
            }
        }
    });

    /**
     * 🔀 Submit BIFURCADO de formDespacho:
     * - Si HAY conductor en selectConductorUnico -> Despacho Directo (ejecutarDespachoDirecto)
     * - Si NO HAY conductor -> Enviar a Cola de Espera (crearCola)
     */
    formDespacho?.addEventListener("submit", async (event) => {
        event.preventDefault();

        // 🛡️ Prevenir submit al dar Enter en inputs intermedios (navegación por campos)
        const elementoActivo = document.activeElement;
        if (elementoActivo && elementoActivo.tagName === "INPUT" && elementoActivo.id !== "btnEnviarDespacho") {
            if (elementoActivo.id === "desNombre") {
                document.getElementById("desOrigen")?.focus();
                document.getElementById("desOrigen")?.select();
            } else if (elementoActivo.id === "desOrigen") {
                const des = document.getElementById("desDestino");
                if (des) {
                    des.disabled = false;
                    des.readOnly = false;
                    des.focus();
                    des.select();
                }
            } else if (elementoActivo.id === "desDestino") {
                document.getElementById("tarifaClienteUnico")?.focus();
                document.getElementById("tarifaClienteUnico")?.select();
            } else if (elementoActivo.id === "tarifaClienteUnico") {
                document.getElementById("selectConductorUnico")?.focus();
            }
            return; 
        }

        if (btnEnviar && btnEnviar.disabled) {
            mostrarToast("⚠️ Complete la información del cliente antes de enviar.", "error");
            return;
        }

        // --------------------------------------------------------------------------
        // 1️⃣ DETERMINAR O REGISTRAR EL CLIENTE (TRANSPARENTE PARA EL OPERADOR)
        // --------------------------------------------------------------------------
        let clienteIdFinal = window.clienteIdActual;

        // Si la bandera está en NULL (cliente nuevo)
        if (!clienteIdFinal) {
            const telNuevo = document.getElementById("desTelefono")?.value.trim();
            const nomNuevo = document.getElementById("desNombre")?.value.trim();
            const oriNuevo = document.getElementById("desOrigen")?.value.trim();

            if (!telNuevo || !nomNuevo || !oriNuevo) {
                mostrarToast("⚠️ Complete Teléfono, Nombre y Origen para continuar", "error");
                return;
            }

            try {
                console.log("🆕 Registrando cliente nuevo en la BD antes del despacho...");
                const resCliente = await apiFetch("/clientes/", {
                    method: "POST",
                    body: JSON.stringify({
                        telefono: telNuevo,
                        nombre: nomNuevo,
                        direccion: oriNuevo
                    })
                });

                clienteIdFinal = resCliente?.id_cliente || resCliente?.cliente_id || resCliente?.id;

                // Búsqueda de respaldo si el backend responde que ya existía
                if (!clienteIdFinal) {
                    const clienteBuscado = await apiFetch(`/clientes/buscar?telefono=${encodeURIComponent(telNuevo)}`);
                    clienteIdFinal = clienteBuscado?.id_cliente || clienteBuscado?.id;
                }

                if (clienteIdFinal) {
                    clienteIdFinal = parseInt(clienteIdFinal);
                    window.clienteIdActual = clienteIdFinal;
                    console.log("✅ Cliente guardado con éxito. ID asignado:", clienteIdFinal);
                } else {
                    throw new Error("No se pudo obtener un ID válido para el cliente.");
                }

            } catch (err) {
                console.error("❌ Error registrando el cliente nuevo:", err);
                mostrarToast("❌ No se pudo guardar la información del cliente nuevo", "error");
                return;
            }
        }

        // --------------------------------------------------------------------------
        // 2️⃣ PROCESAR EL DESPACHO O LA COLA DE ESPERA
        // --------------------------------------------------------------------------
        const selectUnico = document.getElementById("selectConductorUnico");
        const idConductor = selectUnico?.value.trim();

        if (idConductor) {
            // 🟢 CASO A: TIENE CONDUCTOR -> ENVIAR A DESPACHOS ACTIVOS
            console.log("🚀 Despachando a la tabla de despachos activos...");
            
            const optionSel = selectUnico.options[selectUnico.selectedIndex];
            const idAuto = optionSel.dataset.autoId || idConductor;
            
            btnEnviar.disabled = true;
            btnEnviar.innerText = "Procesando...";

            const exito = await ejecutarDespachoDirecto({
                clienteId: parseInt(clienteIdFinal),
                conductorId: parseInt(idConductor),
                autoId: parseInt(idAuto),
                origen: document.getElementById("desOrigen")?.value.trim(),
                destino: document.getElementById("desDestino")?.value.trim(),
                tarifa: parseFloat(document.getElementById("tarifaClienteUnico")?.value || 0),
                idCola: window.idColaEnEdicion || null, // 👈 Se vincula la cola si venía de edición
                optionCondText: optionSel.text
            });

            if (exito) {
                // Si el despacho se procesó desde la cola, eliminamos el registro de la cola
                if (window.idColaEnEdicion) {
                    try {
                        await apiFetch(`/cola_despachos/${window.idColaEnEdicion}`, { method: "DELETE" });
                    } catch (e) { 
                        console.error("Error al eliminar de cola:", e); 
                    }
                    window.idColaEnEdicion = null;
                }

                // Reset de formulario y estados
                document.getElementById("formDespacho").reset();
                window.clienteIdActual = null;
                if (typeof clienteListoParaEnviar !== "undefined") {
                    clienteListoParaEnviar = null;
                }

                if (typeof activarCamposDespacho === "function") {
                    activarCamposDespacho(false);
                }

                // Recargar despacho activo
                if (typeof cargarDespachosActivos === "function") {
                    cargarDespachosActivos();
                }

                document.getElementById("desTelefono")?.focus();
            }

            btnEnviar.disabled = false;
            btnEnviar.innerText = "Enviar Despacho";

        } else {
            // 🟡 CASO B: SIN CONDUCTOR -> ENVIAR A COLA DE ESPERA
            console.log("📋 Enviando a la cola de espera...");

            try {
                const payloadCola = {
                    cliente_id: parseInt(clienteIdFinal),
                    telefono: document.getElementById("desTelefono")?.value.trim(),
                    nombre: document.getElementById("desNombre")?.value.trim(),
                    origen: document.getElementById("desOrigen")?.value.trim(),
                    destino: document.getElementById("desDestino")?.value.trim(),
                    tarifa: parseFloat(document.getElementById("tarifaClienteUnico")?.value || 0)
                };

                const resCola = await apiFetch("/cola_despachos/", {
                    method: "POST",
                    body: JSON.stringify(payloadCola)
                });

                if (resCola && (resCola.id_cola || resCola.id)) {
                    mostrarToast("📋 Cliente en cola de espera", "success");

                    document.getElementById("formDespacho")?.reset();
                    window.clienteIdActual = null;
                    if (typeof clienteListoParaEnviar !== "undefined") {
                        clienteListoParaEnviar = null;
                    }

                    if (typeof activarCamposDespacho === "function") {
                        activarCamposDespacho(false);
                    }

                    if (typeof window.cargarColaClientes === "function") {
                        window.cargarColaClientes();
                    }

                    document.getElementById("desTelefono")?.focus();
                } else {
                    mostrarToast("❌ Error al enviar a la cola: " + (resCola?.error || "Error indeterminado"), "error");
                }
            } catch (err) {
                console.error("❌ Error de red en la cola:", err);
                mostrarToast("❌ Error al enviar a la cola", "error");
            }
        }
    });
    // Botón cancelar sección despacho
    document.getElementById("btnCancelarPrincipal")?.addEventListener("click", () => {
        document.getElementById("formDespacho").reset();
        memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} }; 
        clienteListoParaEnviar = null; 
        activarCamposDespacho(false);
        
        const inputNom = document.getElementById("desNombre");
        if (inputNom) {
            inputNom.readOnly = false;
            inputNom.style.backgroundColor = "#ffffff";
        }

        document.getElementById("desTelefono").focus();
        mostrarToast("🧹 Sistema reseteado para nueva llamada", "info");
    });

    // Botón cancelar modal despacho
    const modal = document.getElementById("modalCrearDespacho");
    const btnCancelar = document.getElementById("btnCancelarDespacho");

    if (btnCancelar) {
        btnCancelar.onclick = () => {
            if (modal) modal.classList.add("hidden");
            console.log("🚫 Despacho cancelado por el usuario");
        };
    }
});

// Listener de teclado global (Alt + C)
document.addEventListener("keydown", (event) => {
    if (event.altKey && (event.key.toLowerCase() === "c" || event.code === "KeyC")) {
        event.preventDefault();
        abrirModalCola();
    }
});


const btnCerrarCola = document.getElementById("btnCerrarCola");
if (btnCerrarCola) {
  btnCerrarCola.addEventListener("click", cerrarModalCola);
}

// ==================== Cola de Clientes (Modal Editable) ====================
window.memoriaEdicionCola1 = window.memoriaEdicionCola1 || {
    origenes: {},
    destinos: {},
    tarifas: {}
};

// Aseguramos la estructura global sin vaciarla en cada llamada
if (typeof window.memoriaEdicionCola1 === "undefined") {
    window.memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} };
}

// 1. CARGAR Y PINTAR LA COLA DE ESPERA
// 1. CARGAR Y PINTAR LA COLA DE ESPERA (VERSIÓN FINAL CORREGIDA)
async function cargarColaClientes() {
    console.log("🔍 Iniciando cargarColaClientes...");

    // 1. Inicializar memorias de edición
    window.memoriaEdicionCola1 = window.memoriaEdicionCola1 || {};
    window.memoriaEdicionCola1.origenes = window.memoriaEdicionCola1.origenes || {};
    window.memoriaEdicionCola1.destinos = window.memoriaEdicionCola1.destinos || {};
    window.memoriaEdicionCola1.tarifas  = window.memoriaEdicionCola1.tarifas || {};

    // 2. Buscar elemento en DOM
    const tbodyCola = document.getElementById("tablaColaClientes");
    if (!tbodyCola) {
        console.warn("⚠️ [DOM] #tablaColaClientes NO existe en este momento. Reintentando en 300ms...");
        setTimeout(window.cargarColaClientes, 300); // Reintento automático si la vista no ha cargado
        return;
    }

    tbodyCola.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-gray-400">Cargando cola...</td></tr>`;

    try {
        console.log("📡 Solicitando datos a /cola_despachos/...");

        // 3. Fallback seguro: Probar apiFetch o fetch con token explicito
        let data;
        if (typeof apiFetch === "function") {
            data = await apiFetch("/cola_despachos/");
        } else {
            const token = localStorage.getItem("token");
            const res = await fetch("/cola_despachos/", {
                headers: {
                    "Authorization": token ? `Bearer ${token}` : "",
                    "Content-Type": "application/json"
                }
            });
            if (!res.ok) throw new Error(`HTTP Error status: ${res.status}`);
            data = await res.json();
        }

        console.log("📦 Datos recibidos del backend:", data);

        // 4. Asegurar que los datos sean un Array (si backend devuelve obj ej: {data: [...]})
        const lista = Array.isArray(data) ? data : (data.cola || data.data || []);

        if (lista.length === 0) {
            tbodyCola.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-gray-400">No hay clientes en cola de espera</td></tr>`;
            return;
        }

        // 5. Renderizar filas
        let htmlFilas = "";
        lista.forEach((c, index) => {
            const id = c.id_cola || c.id;
            const telefono = c.telefono || (c.cliente ? c.cliente.telefono : "---");
            const nombre = c.nombre || (c.cliente ? c.cliente.nombre : "Cliente");
            const origen = c.origen || (c.cliente ? c.cliente.direccion : "");
            const destino = c.destino || "";

            const valOrigen = window.memoriaEdicionCola1.origenes[id] !== undefined ? window.memoriaEdicionCola1.origenes[id] : origen;
            const valDestino = window.memoriaEdicionCola1.destinos[id] !== undefined ? window.memoriaEdicionCola1.destinos[id] : destino;
            const valTarifa = window.memoriaEdicionCola1.tarifas[id] !== undefined ? window.memoriaEdicionCola1.tarifas[id] : (c.tarifa || "");

            htmlFilas += `
            <tr class="hover:bg-gray-50 text-sm border-b">
                <td class="border px-2 py-1 text-center font-bold text-gray-500">${index + 1}</td> 
                <td class="border px-2 py-1 font-mono font-bold text-gray-700">${telefono}</td>
                <td class="border px-2 py-1 font-semibold text-gray-800">${nombre}</td>
                <td class="border px-2 py-1">
                    <input type="text" class="w-full border p-1 rounded bg-yellow-50 focus:bg-white text-center text-xs" 
                        value="${valOrigen}"
                        oninput="window.memoriaEdicionCola1.origenes[${id}] = this.value">
                </td>
                <td class="border px-2 py-1">
                    <input type="text" list="listaTarifasMatriz" class="w-full border p-1 rounded bg-blue-50 focus:bg-white text-center text-xs" 
                        placeholder="Hacia..." 
                        value="${valDestino}" 
                        oninput="window.memoriaEdicionCola1.destinos[${id}] = this.value">
                </td>
                <td class="border px-2 py-1">
                    <input type="number" class="border p-1 w-24 rounded font-bold text-green-700 text-center text-xs"
                        placeholder="COP"
                        value="${valTarifa}"
                        oninput="window.memoriaEdicionCola1.tarifas[${id}] = this.value">
                </td>
                <td class="border px-2 py-1 text-center">
                    <span class="px-2 py-0.5 rounded bg-orange-100 text-xs text-orange-700 font-semibold">${c.estado || 'En espera'}</span>
                </td>
                <td class="border px-2 py-1 flex gap-1 justify-center">
                    <button onclick="prepararAsignacion(${id}, ${c.cliente?.id_cliente || c.cliente_id || id})"
                            class="bg-blue-600 text-white px-2 py-1 rounded text-xs hover:bg-blue-700">
                        Asignar
                    </button>
                    <button onclick="cancelarCliente(${id})"
                            class="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 text-xs">×</button>
                </td>
            </tr>`;
        });

        tbodyCola.innerHTML = htmlFilas;
        console.log("✅ Tabla pintada exitosamente.");

    } catch (err) {
        console.error("❌ Fallo crítico al cargar cola de clientes:", err);
        tbodyCola.innerHTML = `<tr><td colspan="8" class="text-center text-red-500 py-4 font-semibold">Error de conexión con el servidor</td></tr>`;
    }
};
window.cargarColaClientes = cargarColaClientes;
function prepararAsignacion(idCola, idCliente) {
    const selectConductor = document.getElementById("selectConductorUnico") || document.getElementById("nuevoConductor") || document.getElementById("desConductor");
    
    const opcionesValidas = Array.from(selectConductor?.options || []).filter(
        opt => !opt.disabled && opt.value !== ""
    );

    if (opcionesValidas.length === 0) {
        if (typeof mostrarToast === 'function') {
            mostrarToast("⚠️ No hay conductores disponibles para asignar en este momento.", "error");
        } else {
            alert("⚠️ No hay conductores disponibles para asignar en este momento.");
        }
        return; 
    }

    // 1. Buscar la fila (tr) utilizando el idCola buscando cualquier botón que lo contenga
    const botones = Array.from(document.querySelectorAll("button[onclick*='prepararAsignacion']"));
    const btn = botones.find(b => b.getAttribute("onclick").includes(`${idCola},`));
    
    if (!btn) {
        console.warn(`⚠️ No se encontró la fila correspondiente a idCola: ${idCola}`);
        return;
    }
    
    const fila = btn.closest("tr");

    // 2. Extraer los datos directamente de las columnas (children) de la fila
    // [0]: Nro | [1]: Teléfono | [2]: Nombre | [3]: Origen input | [4]: Destino input | [5]: Tarifa input
    const telefonoVal = fila.children[1] ? fila.children[1].textContent.trim() : "";
    const nombreVal   = fila.children[2] ? fila.children[2].textContent.trim() : "";
    
    // Extraer de los inputs internos de cada celda (o fallback a memoria global)
    const inputOrigen  = fila.children[3]?.querySelector("input");
    const inputDestino = fila.children[4]?.querySelector("input");
    const inputTarifa  = fila.children[5]?.querySelector("input");

    const origenVal  = inputOrigen  ? inputOrigen.value  : (window.memoriaEdicionCola1?.origenes?.[idCola] || "");
    const destinoVal = inputDestino ? inputDestino.value : (window.memoriaEdicionCola1?.destinos?.[idCola] || "");
    const tarifaVal  = inputTarifa  ? inputTarifa.value  : (window.memoriaEdicionCola1?.tarifas?.[idCola] || "");

    console.log("🚀 ASIGNANDO DESDE COLA:", { idCola, idCliente, telefonoVal, nombreVal, origenVal, destinoVal, tarifaVal });

    // 3. Inyectar en los campos del formulario superior
    const inputTelForm = document.getElementById("desTelefono");
    const inputNomForm = document.getElementById("desNombre");
    const inputOriForm = document.getElementById("desOrigen");
    const inputDesForm = document.getElementById("desDestino");
    const inputTarForm = document.getElementById("tarifaClienteUnico");
    const inputIdModal = document.getElementById("modalClienteIdDespacho");

    if (inputTelForm) { inputTelForm.value = telefonoVal; inputTelForm.dispatchEvent(new Event('input', { bubbles: true })); }
    if (inputNomForm) { inputNomForm.value = nombreVal; inputNomForm.dispatchEvent(new Event('input', { bubbles: true })); }
    if (inputOriForm) { inputOriForm.value = origenVal; inputOriForm.dispatchEvent(new Event('input', { bubbles: true })); }
    if (inputDesForm) { inputDesForm.value = destinoVal; inputDesForm.dispatchEvent(new Event('input', { bubbles: true })); }
    if (inputTarForm) { inputTarForm.value = tarifaVal; inputTarForm.dispatchEvent(new Event('input', { bubbles: true })); }
    if (inputIdModal) { inputIdModal.value = idCliente; }

    // ⚡ 4. ESTADO DE LISTO
    window.clienteIdActual = idCliente;
    window.clienteListoParaEnviar = { id_cliente: idCliente, nombre: nombreVal, telefono: telefonoVal };

    if (typeof activarCamposDespacho === "function") {
        activarCamposDespacho(true);
    }

    const btnEnviar = document.getElementById("btnEnviarDespacho") || document.querySelector("button[type='submit']");
    if (btnEnviar) {
        btnEnviar.disabled = false;
    }

    window.idColaEnEdicion = idCola;
    window.idClienteEnEdicion = idCliente;

    if (selectConductor) {
        selectConductor.scrollIntoView({ behavior: "smooth", block: "center" });
        selectConductor.focus();
    }
}
let motivoSuspensionGlobal = "";

async function validarClienteExpreso() {
    const telInput = document.getElementById('desTelefono');
    if (!telInput) return { valido: false, motivo: "Input no encontrado" };
    const tel = telInput.value.trim();
    if (!tel) return { valido: false, motivo: "Teléfono vacío" };
    if (document.getElementById('desNombre')) document.getElementById('desNombre').value = "";
    if (document.getElementById('desOrigen')) document.getElementById('desOrigen').value = "";
    if (document.getElementById('desDestino')) document.getElementById('desDestino').value = "";
    try {
        console.log(`📡 [NUEVO] Buscando cliente con teléfono: ${tel}`);
        
        const token = localStorage.getItem("token");
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const response = await fetch(`/clientes/buscar?telefono=${tel}&t=${Date.now()}`, {
            method: "GET",
            headers: headers
        });

        if (!response.ok) {
            return { valido: false, motivo: "Error en el servidor al buscar cliente" };
        }

        const dataCliente = await response.json();
        console.log("🔍 [NUEVO] Datos crudos del cliente:", dataCliente);

        const cliente = Array.isArray(dataCliente) ? dataCliente[0] : dataCliente;
        
        if (cliente) {
            if (document.getElementById('desNombre')) document.getElementById('desNombre').value = cliente.nombre || "";
            
            const inputOrigen = document.getElementById('desOrigen');
            if (inputOrigen) {
                inputOrigen.value = cliente.direccion || "";
                inputOrigen.disabled = false;
                inputOrigen.readOnly = false; // 🔓 Asegura que el origen sea 100% editable
            }

            const inputDestino = document.getElementById('desDestino');
            if (inputDestino) {
                inputDestino.disabled = false;
                inputDestino.readOnly = false; // 🔓 Asegura que el destino esté listo para recibir el salto
            }
            
            window.nombreClienteGlobal = cliente.nombre || "";
            window.telefonoClienteGlobal = cliente.telefono || "";
            window.clienteIdActual = cliente.id_cliente || cliente.id || cliente.cliente_id;

            return { valido: true, cliente: cliente };
        }

        return { valido: false, motivo: "Cliente no registrado" };

    } catch (err) {
        console.error("❌ Error grave en validarClienteExpreso:", err);
        return { valido: false, motivo: "Error de conexión" };
    }
}

function crearToastEmergencia(mensaje, tipo = "VETO") {
    const alertaPrevia = document.getElementById("toast-emergencia");
    if (alertaPrevia) alertaPrevia.remove();

    const div = document.createElement("div");
    div.id = "toast-emergencia";
    div.innerText = mensaje; 
    
    Object.assign(div.style, {
        position: "fixed",
        top: "20px",
        right: "20px",
        backgroundColor: "#ef4444",
        color: "white",
        padding: "16px 24px",
        borderRadius: "8px",
        fontSize: "16px",
        fontWeight: "bold",
        boxShadow: "0px 4px 15px rgba(0,0,0,0.4)",
        zIndex: "999999",
        minWidth: "320px",
        fontFamily: "sans-serif",
        opacity: "0",
        transition: "opacity 0.3s ease-in-out"
    });

    document.body.appendChild(div);
    setTimeout(() => { div.style.opacity = "1"; }, 10);

    setTimeout(() => {
        div.style.opacity = "0";
        setTimeout(() => div.remove(), 350);
    }, 6000);
}

function activarCamposDespacho(activar) {
    // 🛡️ Excluimos intencionalmente 'desOrigen' y 'desDestino' para que NUNCA se bloqueen solos
    const campos = ["desNombre", "btnEnviarDespacho", "btnModificarCliente"];
    
    campos.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.disabled = !activar;
            el.classList.toggle("bg-gray-100", !activar);
            el.classList.toggle("cursor-not-allowed", !activar);
        }
    });

    // Nos aseguramos de que el origen y destino siempre estén listos y operativos
    const origen = document.getElementById("desOrigen");
    if (origen) {
        origen.disabled = false;
        origen.readOnly = false;
    }

    const destino = document.getElementById("desDestino");
    if (destino) {
        destino.disabled = false;
        destino.readOnly = false;
    }
}

async function cancelarCliente(idCola) {
    if (!confirm("¿Estás seguro de que deseas eliminar a este cliente de la cola?")) {
        return;
    }

    try {
        const result = await apiFetch(`/cola_despachos/${idCola}`, {
            method: "DELETE"
        });

        if (result.error) {
            mostrarToast("❌ No se pudo cancelar: " + result.error, "error");
        } else {
            mostrarToast("🗑️ Cliente eliminado de la cola", "info");
            await cargarColaClientes();
        }
    } catch (err) {
        console.error("Error al cancelar cliente:", err);
        mostrarToast("❌ Error de conexión al intentar cancelar", "error");
    }
}

async function actualizarContadorConductores() {
    try {
        const res = await apiFetch("/conductores/en_turno_disponibles");
        const data = (res && typeof res.json === 'function') ? await res.json() : res;
        
        const totalDisponibles = Array.isArray(data) ? data.length : 0;
        const badge = document.getElementById("contadorConductores");
        
        if (badge) {
            badge.innerText = `Conductores disponibles: ${totalDisponibles}`;
            badge.className = totalDisponibles > 0 
                ? "bg-green-100 text-green-800 text-xs font-bold px-2.5 py-1 rounded border border-green-500"
                : "bg-red-100 text-red-800 text-xs font-bold px-2.5 py-1 rounded border border-red-500";
        }
    } catch (error) {
        console.error("Error al contar conductores:", error);
    }
}

// 🚀 Genera el datalist y soporta carga desde la API o variable global
// 1. Petición al endpoint de Flask
async function cargarMatrizTarifas() {
    try {
        const res = await fetch('/obtener_tarifas');
        if (!res.ok) throw new Error("Respuesta de servidor no OK");
        
        window.MATRIZ_TARIFAS = await res.json();
        console.log(`📦 Se recibieron ${window.MATRIZ_TARIFAS.length} tarifas desde la BD.`);
        
        generarDatalistTarifas();
    } catch (err) {
        console.error("❌ Error al cargar tarifas:", err);
    }
}

// 2. Poblado de las opciones en el <datalist id="listaTarifasMatriz">
function generarDatalistTarifas() {
    // Lee la variable global inyectada por Jinja2
    const matriz = window.MATRIZ_TARIFAS;

    if (!matriz || !Array.isArray(matriz) || matriz.length === 0) {
        console.warn("⚠️ MATRIZ_TARIFAS no está disponible o viene vacía desde Jinja2.");
        return;
    }

    const datalist = document.getElementById("listaTarifasMatriz");
    if (!datalist) {
        console.error("❌ No se encontró el elemento #listaTarifasMatriz en el HTML.");
        return;
    }

    // Generar opciones con el nombre exacto de las claves que envía Jinja2 (destino, precio_cop/precio_bs, municipio)
    let htmlOptions = "";
    matriz.forEach(t => {
        const dest = t.destino || "";
        const precio = parseInt(t.precio_cop || t.precio_bs || t.precio || 0);
        const mun = t.municipio ? `${t.municipio} - ` : "";

        if (dest) {
            htmlOptions += `<option value="${dest}">${mun}${precio} COP</option>`;
        }
    });

    datalist.innerHTML = htmlOptions;
    console.log(`✅ ¡Éxito! ${datalist.children.length} destinos cargados en #listaTarifasMatriz`);

    // Vincular autocompletado de tarifa al escribir o elegir destino
    const inputDestino = document.getElementById("desDestino");
    if (inputDestino && !inputDestino.dataset.listenerListo) {
        inputDestino.dataset.listenerListo = "true"; // Evita duplicar escuchadores

        inputDestino.addEventListener("input", (e) => {
            const val = e.target.value.trim().toLowerCase();
            if (!val) return;

            const encontrado = window.MATRIZ_TARIFAS.find(
                t => (t.destino || "").toLowerCase() === val
            );

            if (encontrado) {
                const inputTarifa = document.getElementById("tarifaClienteUnico");
                if (inputTarifa) {
                    const precioFinal = parseInt(encontrado.precio_cop || encontrado.precio_bs || encontrado.precio || 0);
                    inputTarifa.value = precioFinal;

                    if (typeof mostrarToast === "function") {
                        mostrarToast(`💡 Tarifa: ${precioFinal} COP`, "info");
                    }
                }
            }
        });
    }
}
function actualizarPrecio(input, idFila) {
    if (typeof MATRIZ_TARIFAS === 'undefined') return;
    const destinoSeleccionado = input.value;
    const datos = MATRIZ_TARIFAS.find(t => t.destino === destinoSeleccionado);
    
    if (datos) {
        const inputPrecio = document.getElementById(`tarifa_${idFila}`);
        if (inputPrecio) inputPrecio.value = datos.precio_cop;
        console.log(`💰 Precio actualizado para ${datos.destino}: ${datos.precio_cop} COP`);
    }
}
// 🚀 INICIALIZACIÓN ÚNICA Y SECUENCIAL DE TODO EL FORMULARIO DE DESPACHO
// 🚀 INICIALIZACIÓN ÚNICA Y SECUENCIAL DE TODO EL FORMULARIO DE DESPACHO
document.addEventListener("DOMContentLoaded", () => {
    // 1. Generar datalist de tarifas e inicializar la cola de clientes
    const inputDestino = document.getElementById("desDestino");
    
    if (inputDestino) {
        inputDestino.addEventListener("input", (e) => {
            const val = e.target.value.trim().toLowerCase();
            if (!val || !window.MATRIZ_TARIFAS) return;

            const encontrado = window.MATRIZ_TARIFAS.find(
                t => (t.destino || "").toLowerCase() === val
            );

            if (encontrado) {
                const inputTarifa = document.getElementById("tarifaClienteUnico");
                if (inputTarifa) {
                    const precioFinal = parseInt(encontrado.precio_cop || encontrado.precio_bs || encontrado.precio || 0);
                    inputTarifa.value = precioFinal;

                    if (typeof mostrarToast === "function") {
                        mostrarToast(`💡 Tarifa: ${precioFinal} COP`, "info");
                    }
                }
            }
        });
    }

    setTimeout(() => {
        if (typeof cargarColaClientes === "function") {
            cargarColaClientes();
        }
    }, 100);

    const tel = document.getElementById("desTelefono");
    const nom = document.getElementById("desNombre");
    const ori = document.getElementById("desOrigen");
    const des = document.getElementById("desDestino");
    const tarifa = document.getElementById("tarifaClienteUnico");
    const selectConductor = document.getElementById("selectConductorUnico") || document.getElementById("nuevoConductor");

    // 2. Secuencia de salto limpia con la tecla Enter (campo por campo)
    tel?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
        }
    });

    nom?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            ori?.focus();
            ori?.select();
        }
    });

    // 🛡️ Salto universal de Origen a Destino (Sirve para nuevos y existentes)
    ori?.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.keyCode === 13) {
            e.preventDefault(); // Frena cualquier envío loco del formulario
            
            const inputDestino = document.getElementById("desDestino");
            if (inputDestino) {
                inputDestino.disabled = false;
                inputDestino.readOnly = false;
                inputDestino.focus();
                inputDestino.select();
                console.log("➡️ Salto exitoso de Origen a Destino.");
            }
        }
    });

    des?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            tarifa?.focus();
            tarifa?.select();
        }
    });

    tarifa?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            selectConductor?.focus();
        }
    });

    // 3. Lógica del Enter final en el selector de conductores
    if (selectConductor) {
        selectConductor.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.keyCode === 13) {
                event.preventDefault();

                const valorSelect = selectConductor.value ? selectConductor.value.trim() : "";
                const formDespacho = document.getElementById("formDespacho");

                const hayConductorSeleccionado = valorSelect !== "" && valorSelect !== "null" && valorSelect !== "undefined";

                if (hayConductorSeleccionado) {
                    // 🟢 CASO A: Hay un conductor elegido -> Despacho directo
                    console.log("🚀 Enter con conductor seleccionado. Enviando despacho directo...");
                    if (formDespacho) {
                        formDespacho.requestSubmit ? formDespacho.requestSubmit() : formDespacho.submit();
                    }
                } 
                else {
                    // 🟡 CASO B: Select vacío O 0 conductores disponibles -> Enviamos a la cola de espera
                    console.log("📋 Sin conductor seleccionado (o 0 disponibles). Enviando a la cola de espera...");
                    if (formDespacho) {
                        formDespacho.requestSubmit ? formDespacho.requestSubmit() : formDespacho.submit();
                    }
                }
            }
        });
    }
});