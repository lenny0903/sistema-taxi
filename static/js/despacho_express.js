// ==================== Bloque 1: Flujo rápido (alta demanda) ====================
let memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} };
// * 🟢 Función Global para llenar el selectConductorUnico
// * Mapea resilientemente los campos del backend (codigo/numero_control, id_conductor, nombre)
// */
window.llenarSelectConductoresUnico = function(conductoresEnTurno) {
    const selectCond = document.getElementById("selectConductorUnico");
    const contadorSpan = document.getElementById("contadorConductores"); // 👈 Capturamos el span del HTML
    
    if (!selectCond) {
        console.warn("⚠️ No se encontró el elemento <select id='selectConductorUnico'>.");
        return;
    }

    // Mantener la opción por defecto para enviar a la cola
    selectCond.innerHTML = '<option value="">-- Sin Conductor (Enviar a Cola) --</option>';

    if (!Array.isArray(conductoresEnTurno) || conductoresEnTurno.length === 0) {
        console.warn("⚠️ No hay conductores en turno disponibles actualmente.");
        selectCond.selectedIndex = 0;
        
        // 🔢 Si no hay conductores, actualiza a 0
        if (contadorSpan) {
            contadorSpan.textContent = "Conductores disponibles: 0";
        }
        return;
    }

    let contador = 0;
    conductoresEnTurno.forEach(item => {
        // Extraer los sub-objetos devueltos por /en_turno_disponibles
        const c = item.conductor;
        const a = item.auto;

        // Validar que exista el objeto conductor
        if (c && c.id_conductor) {
            const option = document.createElement("option");
            
            const idConductor = c.id_conductor;
            const idAuto = a ? a.id_auto : "";
            const nroControl = c.codigo || "S/C";
            const nombre = c.nombre || "Conductor";

            option.value = idConductor;
            if (idAuto) {
                option.dataset.autoId = idAuto;
            }
            
            // Texto formateado: [B15] Pedro Pérez
            option.textContent = `[${nroControl}] ${nombre}`;

            selectCond.appendChild(option);
            contador++;
        }
    });

   selectCond.selectedIndex = 0;

    // 🚀 Actualiza dinámicamente el badge en la interfaz
    if (contadorSpan) {
        contadorSpan.textContent = `Conductores disponibles: ${contador}`;
    }

    console.log(`✅ Select Express poblado exitosamente con ${contador} conductor(es) en turno disponible(s).`);
};
// * 📡 Consulta autosuficiente para cargar únicamente los conductores EN TURNO

async function refrescarSelectConductorUnico() { 
    try { 
        // ⚡ Consumimos el endpoint de conductores EN TURNO y LIBRES (sin despacho en curso)
        const data = await apiFetch('/conductores/en_turno_disponibles'); 
        console.log("📡 [EXPRESS] Conductores en turno recibidos:", data); 

        let listaData = Array.isArray(data) ? data : []; 
        window.llenarSelectConductoresUnico(listaData); 
    } catch (err) { 
        console.error("❌ [EXPRESS] Error al refrescar selectConductorUnico en turno:", err); 
    } 
}
window.refrescarSelectConductorUnico = refrescarSelectConductorUnico;
/**
 * 🚀 Función centralizada reutilizable para procesar Despachos Directos
 * Maneja validación de afinidad, API POST /despachos/ y creación del banner flotante.
 */
window.isDespachandoFlag = false;

async function ejecutarDespachoDirecto({ 
    clienteId, 
    conductorId, 
    autoId, 
    origen, 
    destino, 
    tarifa, 
    idCola = null, 
    optionCondText = "",
    nroControl = null // 👈 Si lo tienes disponible, puedes pasarlo; si no, se deduce abajo
}) {
    if (window.isDespachandoFlag) {
        console.warn("⚠️ Ejecución de despacho ya en curso. Ignorando evento duplicado.");
        return false;
    }

    if (!origen || !tarifa) {
        mostrarToast("⚠️ El origen y la tarifa son obligatorios", "error");
        return false;
    }

    if (!clienteId || !conductorId) {
        mostrarToast("⚠️ Datos de cliente o conductor incompletos", "error");
        return false;
    }

    window.isDespachandoFlag = true;

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
            window.isDespachandoFlag = false;
            return false; 
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

            // 📲 3. GENERAR BANNER FLOTANTE (Protegido en bloque independiente)
            try {
                const inputNombre = document.getElementById("desNombre") || document.getElementById("modalNombreCliente");
                const inputTelefono = document.getElementById("desTelefono") || document.getElementById("modalTelefonoCliente");
                
                const nombreCliente = window.nombreClienteGlobal || (inputNombre ? inputNombre.value.trim() : "Cliente");
                const telefonoCliente = result.cliente_telefono || (inputTelefono ? inputTelefono.value.trim() : "") || "";

                // 🎯 Resolver nroControl de forma segura si no vino por parámetro
                const matchDigitos = optionCondText.match(/\d+/);
                const numClean = matchDigitos ? matchDigitos[0] : "1";
                const numFormateado = numClean.padStart(2, '0');
                const nroControlCalculado = nroControl || `B${numClean}`;

                const nombreArchivoFlayer = `B${numFormateado}.png`;
                const rutaFlayerLocal = `/static/img/flayers/${nombreArchivoFlayer}`;
                
                const nombreCond = optionCondText.includes(' - ') ? optionCondText.split(' - ')[1] : optionCondText || "Conductor";
                const enlaceBotTelegram = `https://t.me/Lospatriotas_bot?text=UBI`;

                const msgCliente = 
                    `¡Hola! 🚖 Su servicio ha sido procesado con éxito.\n\n` +
                    `📍 *Para ver el mapa y rastrear su unidad en tiempo real, haga clic aquí:*\n` +
                    `${enlaceBotTelegram}\n\n` +
                    `*(O busque el bot @Lospatriotas_bot en Telegram y envíe la palabra UBI)*`;
                const nroControlConductor = nroControlCalculado !== "B1" ? nroControlCalculado : optionCondText;

                const msgConductor = 
                    `🚖 *NUEVO DESPACHO ASIGNADO* (#${result.id_despacho})\n\n` +
                    `📍 *Origen:* ${origen}\n` +
                    `🏁 *Destino:* ${destino}\n` +
                    `💰 *Tarifa:* ${tarifa ? tarifa + ' COP' : 'A convenir'}\n` +
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
                    <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 12px; flex-wrap: wrap;">
                        
                        <!-- 📌 BLOQUE DE INFORMACIÓN (Referencia visual clara para el operador) -->
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <img src="${rutaFlayerLocal}" alt="Flayer" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover; border: 2px solid #25d366; background: #444;" onerror="this.src='https://via.placeholder.com/40?text=🚗'">
                            <div>
                                <div style="font-weight: bold; font-size: 13px; color: #fff;">
                                    Despacho #${result.id_despacho} <span style="font-weight: normal; color: #25d366; font-size: 12px;">(Unidad #${nroControlConductor})</span>
                                </div>
                                <div style="font-size: 11px; color: #bbb;">
                                    👤 ${nombreCliente} &nbsp;|&nbsp; 📱 ${window.telefonoClienteGlobal || telefonoCliente}
                                </div>
                                <div style="font-size: 11px; color: #fbbf24; margin-top: 2px; max-width: 450px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="Origen: ${document.getElementById('desOrigen')?.value || 'N/A'} | Destino: ${document.getElementById('desDestino')?.value || 'N/A'}">
                                    📍 <b>Org:</b> ${document.getElementById('desOrigen')?.value || 'N/A'} &nbsp;|&nbsp; 🏁 <b>Dst:</b> ${document.getElementById('desDestino')?.value || 'N/A'}
                                </div>
                            </div>
                        </div>

                        <!-- 🕹️ BOTONES DE ACCIÓN COMPACTOS -->
                        <div style="display: flex; gap: 6px; align-items: center;">
                            <button id="btnCli" type="button" tabindex="-1" style="background: #25d366; color: white; border: none; padding: 5px 9px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;" title="Copiar imagen del flayer">
                                🖼️ Flayer
                            </button>
                            <button id="btnTextoCli" type="button" tabindex="-1" style="background: #0088cc; color: white; border: none; padding: 5px 9px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;" title="Copiar texto para el cliente">
                                💬 Texto Cliente
                            </button>
                            <button id="btnCond" type="button" tabindex="-1" style="background: #128c7e; color: white; border: none; padding: 5px 9px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500;" title="Copiar mensaje para el conductor">
                                🚗 Conductor
                            </button>
                            <button id="btnCerrarBanner" type="button" tabindex="-1" style="background: transparent; color: #aaa; border: none; padding: 4px 6px; cursor: pointer; font-size: 16px;" title="Cerrar banner">✕</button>
                        </div>

                    </div>
                `;
                document.body.appendChild(bannerDiv);

                if (document.activeElement) {
                    document.activeElement.blur();
                }

                const btnCli = bannerDiv.querySelector('#btnCli');
                btnCli.addEventListener('keydown', (e) => { if (e.key === 'Enter') e.preventDefault(); });

                btnCli.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    try {
                        // Intentamos cargar la ruta principal
                        let response = await fetch(rutaFlayerLocal);
                        
                        // Si da 404, intentamos buscar si el archivo existe con otra extensión común (.jpeg o .jpg)
                        if (response.status === 404) {
                            // Reemplazamos .png por .jpeg o .jpg según corresponda
                            let rutaAlternativa = rutaFlayerLocal.replace(/\.png$/i, '.jpeg');
                            response = await fetch(rutaAlternativa);
                            
                            if (response.status === 404) {
                                rutaAlternativa = rutaFlayerLocal.replace(/\.png$/i, '.jpg');
                                response = await fetch(rutaAlternativa);
                            }
                        }

                        // Si después de buscar alternativas sigue dando 404, mostramos el aviso original
                        if (response.status === 404) {
                            mostrarToast(`ℹ️ La imagen ${nombreArchivoFlayer} no existe en /static/img/flayers/`, "warning");
                            return;
                        }

                        if (!response.ok) throw new Error(`Error en el servidor: ${response.status}`);

                        const rawBlob = await response.blob();
                        let finalPngBlob = rawBlob;

                        if (rawBlob.type !== "image/png") {
                            const img = new Image();
                            img.crossOrigin = "anonymous";
                            await new Promise((resolve, reject) => {
                                img.onload = resolve;
                                img.onerror = () => reject(new Error("No se pudo procesar la imagen"));
                                img.src = URL.createObjectURL(rawBlob);
                            });

                            const canvas = document.createElement("canvas");
                            canvas.width = img.naturalWidth || img.width;
                            canvas.height = img.naturalHeight || img.height;
                            const ctx = canvas.getContext("2d");
                            ctx.drawImage(img, 0, 0);

                            finalPngBlob = await new Promise(res => canvas.toBlob(res, "image/png"));
                        }

                        await navigator.clipboard.write([
                            new ClipboardItem({ "image/png": finalPngBlob })
                        ]);

                        mostrarToast(`🖼️ Flayer ${nombreArchivoFlayer} copiado`, "success");

                    } catch (err) {
                        mostrarToast(`⚠️ Error al copiar: ${err.message || err}`, "error");
                    }
                });

                bannerDiv.querySelector('#btnTextoCli').addEventListener('click', async (e) => {
                    e.preventDefault();
                    try {
                        await navigator.clipboard.writeText(msgCliente);
                        mostrarToast("📋 Mensaje cliente copiado", "success");
                    } catch (err) {
                        mostrarToast("⚠️ No se pudo copiar el texto", "error");
                    }
                });

                bannerDiv.querySelector('#btnCond').addEventListener('click', async (e) => {
                    e.preventDefault();
                    try {
                        await navigator.clipboard.writeText(msgConductor);
                        mostrarToast("📋 Mensaje conductor copiado", "success");
                    } catch (err) {
                        mostrarToast("⚠️ No se pudo copiar", "error");
                    }
                });

                bannerDiv.querySelector('#btnCerrarBanner').addEventListener('click', (e) => {
                    e.preventDefault();
                    bannerDiv.remove();
                });

            } catch (bannerErr) {
                console.error("⚠️ Error manipulando el banner flotante:", bannerErr);
            }

            // 🔄 4. Refresco asíncrono no bloqueante
            setTimeout(() => {
                Promise.allSettled([
                    typeof cargarColaClientes === 'function' ? cargarColaClientes() : Promise.resolve(),
                    typeof refrescarSelectConductorUnico === 'function' ? refrescarSelectConductorUnico() : Promise.resolve(),
                    typeof refrescarConductoresDisponibles === 'function' ? refrescarConductoresDisponibles() : Promise.resolve()
                ]).finally(() => {
                    window.isDespachandoFlag = false;
                });
            }, 50);

            return true;
        } else {
            mostrarToast("❌ Error: " + (result.error || "No se pudo crear el despacho"), "error");
            window.isDespachandoFlag = false;
            return false;
        }
    } catch (err) {
        console.error("❌ Error en Despacho:", err);
        mostrarToast("❌ Error de conexión o del servidor", "error");
        window.isDespachandoFlag = false;
        return false;
    }
}
document.addEventListener("DOMContentLoaded", () => {
    // --------------------------------------------------------------------------
    // 1. REFERENCIAS AL DOM
    // --------------------------------------------------------------------------
    const formDespacho = document.getElementById("formDespacho");
    const telefonoInput = document.getElementById("desTelefono");
    const nomInput = document.getElementById("desNombre");
    const oriInput = document.getElementById("desOrigen");
    const desInput = document.getElementById("desDestino");
    const tarifaInput = document.getElementById("tarifaClienteUnico");
    const btnEnviar = document.getElementById("btnEnviarDespacho");
    const selectConductor = document.getElementById("selectConductorUnico") || document.getElementById("nuevoConductor");

    let clienteListoParaEnviar = null; 

    if (btnEnviar) btnEnviar.disabled = true;

    // Carga inicial de datos
    if (typeof refrescarSelectConductorUnico === "function") {
        refrescarSelectConductorUnico();
    }
    
    setTimeout(() => {
        if (typeof cargarColaClientes === "function") {
            cargarColaClientes();
        }
    }, 100);

    // --------------------------------------------------------------------------
    // 2. MATRIZ DE TARIFAS AUTOMÁTICA (Al escribir en Destino)
    // --------------------------------------------------------------------------
    if (desInput) {
        desInput.addEventListener("input", (e) => {
            const val = e.target.value.trim().toLowerCase();
            if (!val || !window.MATRIZ_TARIFAS) return;

            const encontrado = window.MATRIZ_TARIFAS.find(
                t => (t.destino || "").toLowerCase() === val
            );

            if (encontrado && tarifaInput) {
                const precioFinal = parseInt(encontrado.precio_cop || encontrado.precio_bs || encontrado.precio || 0);
                tarifaInput.value = precioFinal;

                if (typeof mostrarToast === "function") {
                    mostrarToast(`💡 Tarifa: ${precioFinal} COP`, "info");
                }
            }
        });
    }

    // --------------------------------------------------------------------------
    // 3. NAVEGACIÓN Y FLUJO POR TECLADO (ENTER Y TAB)
    // --------------------------------------------------------------------------
    
    // De Nombre -> Origen
    nomInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            oriInput?.focus();
            oriInput?.select();
        }
    });

    // De Origen -> Destino
    oriInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.keyCode === 13) {
            e.preventDefault();
            if (desInput) {
                desInput.disabled = false;
                desInput.readOnly = false;
                desInput.focus();
                desInput.select();
            }
        }
    });

    // De Destino -> Tarifa
    desInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            tarifaInput?.focus();
            tarifaInput?.select();
        }
    });

    // De Tarifa -> Select Conductor
    tarifaInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            if (selectConductor && selectConductor.options.length > 1) {
                selectConductor.focus();
            } else if (btnEnviar) {
                // Si no hay conductores en la lista, ir directo a Enviar
                activarBotonEnviar(btnEnviar);
                btnEnviar.focus();
            }
        }
    });

    // 🛡️ CONTROL TOTAL EN SELECT CONDUCTOR (Bloquea el salto al botón Limpiar)
    if (selectConductor) {
        selectConductor.addEventListener("keydown", (e) => {
            // Manejar tanto TAB como ENTER para que salte al botón Enviar
            if (e.key === "Tab" || e.key === "Enter" || e.keyCode === 13) {
                e.preventDefault();
                e.stopPropagation();

                if (btnEnviar) {
                    activarBotonEnviar(btnEnviar);
                    btnEnviar.focus();

                    // Si presionó Enter dentro del select, de una vez presiona el botón
                    if (e.key === "Enter" || e.keyCode === 13) {
                        btnEnviar.click();
                    }
                }
            }
        });
    }

    // Función auxiliar para habilitar visual y funcionalmente el botón
    function activarBotonEnviar(btn) {
        btn.disabled = false;
        btn.removeAttribute("disabled");
        btn.classList.remove("opacity-50", "cursor-not-allowed");
    }

    // --------------------------------------------------------------------------
    // 4. VALIDACIÓN ASÍNCRONA DEL TELÉFONO
    // --------------------------------------------------------------------------
    telefonoInput?.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            const telActual = telefonoInput.value.trim();
            if (telActual === "") {
                event.preventDefault();
                event.stopImmediatePropagation();
                return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();

            if (!telefonoInput.checkValidity()) {
                if (typeof mostrarToast === "function") mostrarToast("⚠️ " + telefonoInput.validationMessage, "error");
                telefonoInput.reportValidity();
                return; 
            }

            if (clienteListoParaEnviar === telActual && nomInput && nomInput.value.trim() !== "") {
                if (desInput) desInput.focus();
                return;
            }

            if (nomInput) nomInput.value = "Buscando..."; 
            if (oriInput) oriInput.value = "Buscando..."; 
            if (desInput) desInput.value = ""; 

            if (typeof refrescarSelectConductorUnico === "function") {
                refrescarSelectConductorUnico();
            }

            const resultado = await validarClienteExpreso();
            
            if (resultado && resultado.valido === true && resultado.cliente) {
                const c = resultado.cliente;
                
                if (nomInput) {
                    nomInput.value = c.nombre || "";
                    nomInput.readOnly = true;
                    nomInput.style.backgroundColor = "#f3f4f6"; 
                }
                if (oriInput) {
                    oriInput.value = c.direccion || "";
                    oriInput.disabled = false;
                    oriInput.readOnly = false;
                    oriInput.style.backgroundColor = "#f3f4f6";
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
               
                if (desInput) {
                    desInput.disabled = false;
                    desInput.readOnly = false;
                    desInput.style.backgroundColor = "#ffffff";
                    desInput.value = ""; 
                    desInput.focus(); 
                }

                clienteListoParaEnviar = telActual; 
                if (btnEnviar) activarBotonEnviar(btnEnviar);

            } else {
                if (typeof mostrarToast === 'function') {
                    mostrarToast("✨ Cliente nuevo. Ingresa el nombre y origen.", "info");
                }

                if (nomInput) {
                    nomInput.disabled = false;     
                    nomInput.readOnly = false;     
                    nomInput.value = "";
                    nomInput.style.backgroundColor = "#ffffff";
                }

                if (oriInput) {
                    oriInput.disabled = false;     
                    oriInput.readOnly = false;
                    oriInput.value = "";
                    oriInput.style.backgroundColor = "#ffffff";
                }

                if (desInput) {
                    desInput.disabled = false;
                    desInput.readOnly = false;
                }

                window.clienteIdActual = null;
                clienteListoParaEnviar = telActual; 
                if (btnEnviar) activarBotonEnviar(btnEnviar);

                telefonoInput.blur();
                setTimeout(() => {
                    if (nomInput) {
                        nomInput.focus();
                        nomInput.select();
                    }
                }, 50);
            }
        }
    });

    // --------------------------------------------------------------------------
    // 5. ENVÍO DEL FORMULARIO (SUBMIT A BASE DE DATOS O COLA)
    // --------------------------------------------------------------------------
    formDespacho?.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (window.semaforoRojo) {
            if (typeof mostrarToast === "function") mostrarToast("🚫 Operación bloqueada por Veto General del cliente", "error");
            return;
        }

        if (btnEnviar && btnEnviar.disabled) {
            if (typeof mostrarToast === "function") mostrarToast("⚠️ Complete la información del cliente antes de enviar.", "error");
            return;
        }

        // Registrar o verificar cliente
        let clienteIdFinal = window.clienteIdActual;

        if (!clienteIdFinal) {
            const telNuevo = telefonoInput?.value.trim();
            const nomNuevo = nomInput?.value.trim();
            const oriNuevo = oriInput?.value.trim();

            if (!telNuevo || !nomNuevo || !oriNuevo) {
                if (typeof mostrarToast === "function") mostrarToast("⚠️ Complete Teléfono, Nombre y Origen para continuar", "error");
                return;
            }

            try {
                const resCliente = await apiFetch("/clientes/", {
                    method: "POST",
                    body: JSON.stringify({
                        telefono: telNuevo,
                        nombre: nomNuevo,
                        direccion: oriNuevo
                    })
                });

                clienteIdFinal = resCliente?.id_cliente || resCliente?.cliente_id || resCliente?.id;

                if (!clienteIdFinal) {
                    const clienteBuscado = await apiFetch(`/clientes/buscar?telefono=${encodeURIComponent(telNuevo)}`);
                    clienteIdFinal = clienteBuscado?.id_cliente || clienteBuscado?.id;
                }

                if (clienteIdFinal) {
                    clienteIdFinal = parseInt(clienteIdFinal);
                    window.clienteIdActual = clienteIdFinal;
                } else {
                    throw new Error("No se pudo obtener un ID válido para el cliente.");
                }

            } catch (err) {
                console.error("❌ Error registrando cliente nuevo:", err);
                if (typeof mostrarToast === "function") mostrarToast("❌ No se pudo guardar la información del cliente", "error");
                return;
            }
        }

        // Ejecutar despacho activo o mandar a Cola
        const idConductor = selectConductor?.value.trim();

        if (idConductor) {
            const optionSel = selectConductor.options[selectConductor.selectedIndex];
            const idAuto = optionSel.dataset.autoId || idConductor;
            
            btnEnviar.disabled = true;
            btnEnviar.innerText = "Procesando...";

            const exito = await ejecutarDespachoDirecto({
                clienteId: parseInt(clienteIdFinal),
                conductorId: parseInt(idConductor),
                autoId: parseInt(idAuto),
                origen: oriInput?.value.trim(),
                destino: desInput?.value.trim(),
                tarifa: parseFloat(tarifaInput?.value || 0),
                idCola: window.idColaEnEdicion || null,
                optionCondText: optionSel.text
            });

            if (exito) {
                if (window.idColaEnEdicion) {
                    try {
                        await apiFetch(`/cola_despachos/${window.idColaEnEdicion}`, { method: "DELETE" });
                    } catch (e) { console.error("Error al eliminar de cola:", e); }
                    window.idColaEnEdicion = null;
                }

                formDespacho.reset();
                window.clienteIdActual = null;
                clienteListoParaEnviar = null;

                if (typeof activarCamposDespacho === "function") activarCamposDespacho(false);
                if (typeof cargarDespachosActivos === "function") cargarDespachosActivos();

                telefonoInput?.focus();
            }

            btnEnviar.disabled = false;
            btnEnviar.innerText = "Enviar Despacho";

        } else {
            // Guardar en cola de espera
            try {
                const payloadCola = {
                    cliente_id: parseInt(clienteIdFinal),
                    telefono: telefonoInput?.value.trim(),
                    nombre: nomInput?.value.trim(),
                    origen: oriInput?.value.trim(),
                    destino: desInput?.value.trim(),
                    tarifa: parseFloat(tarifaInput?.value || 0)
                };

                const resCola = await apiFetch("/cola_despachos/", {
                    method: "POST",
                    body: JSON.stringify(payloadCola)
                });

                if (resCola && (resCola.id_cola || resCola.id)) {
                    if (typeof mostrarToast === "function") mostrarToast("📋 Cliente en cola de espera", "success");

                    formDespacho?.reset();
                    window.clienteIdActual = null;
                    clienteListoParaEnviar = null;

                    if (typeof activarCamposDespacho === "function") activarCamposDespacho(false);
                    if (typeof window.cargarColaClientes === "function") window.cargarColaClientes();

                    telefonoInput?.focus();
                } else {
                    if (typeof mostrarToast === "function") mostrarToast("❌ Error al enviar a la cola", "error");
                }
            } catch (err) {
                console.error("❌ Error de red en la cola:", err);
                if (typeof mostrarToast === "function") mostrarToast("❌ Error al enviar a la cola", "error");
            }
        }
    });

    // --------------------------------------------------------------------------
    // 6. BOTONES DE CANCELAR
    // --------------------------------------------------------------------------
    document.getElementById("btnCancelarPrincipal")?.addEventListener("click", () => {
        formDespacho.reset();
        memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} }; 
        clienteListoParaEnviar = null; 
        if (typeof activarCamposDespacho === "function") activarCamposDespacho(false);

        if (nomInput) {
            nomInput.readOnly = false;
            nomInput.style.backgroundColor = "#ffffff";
        }

        telefonoInput?.focus();
        if (typeof mostrarToast === "function") mostrarToast("🧹 Sistema reseteado para nueva llamada", "info");
    });

    const modal = document.getElementById("modalCrearDespacho");
    const btnCancelar = document.getElementById("btnCancelarDespacho");

    if (btnCancelar) {
        btnCancelar.onclick = () => {
            if (modal) modal.classList.add("hidden");
        };
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
                inputOrigen.readOnly = false;
            }

            const inputDestino = document.getElementById('desDestino');
            if (inputDestino) {
                inputDestino.disabled = false;
                inputDestino.readOnly = false;
            }
            
            window.nombreClienteGlobal = cliente.nombre || "";
            window.telefonoClienteGlobal = cliente.telefono || "";
            window.clienteIdActual = cliente.id_cliente || cliente.id || cliente.cliente_id;

            // 🛑 Consultar e interpretar incidencias ANTES de continuar
            try {
                // 🛡️ Asegurar headers con JWT token
                const token = localStorage.getItem('token') || localStorage.getItem('access_token');
                const misHeaders = {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                };

                // 🎯 RUTA CORRECTA SEGÚN TU BACKEND FLASK: /incidencias/verificar_cliente/ID
                // (Si tu Blueprint está registrado con prefijo '/incidencias', usa '/incidencias/verificar_cliente/...')
                const resIncidencias = await fetch(`/incidencias/verificar_cliente/${window.clienteIdActual}?t=${Date.now()}`, { 
                    headers: misHeaders 
                });
                
                if (resIncidencias.ok) {
                    const check = await resIncidencias.json();
                    console.log("🛑 Resumen de incidencias recibido del backend:", check);

                    // 1. Bloqueo Absoluto (VETO GENERAL / NO PAGO)
                    if (check && check.tiene_veto_general === true) {
                        window.semaforoRojo = true; // 🔴 Bloquea despacho
                        const msgVeto = `🚫 VETO GENERAL: ${check.mensaje_veto || check.descripcion || 'Cliente suspendido'}`;
                        
                        if (typeof crearToastEmergencia === "function") {
                            crearToastEmergencia(msgVeto);
                        } else if (typeof mostrarToast === "function") {
                            mostrarToast(msgVeto, "error");
                        }
                    } else {
                        window.semaforoRojo = false; // 🔓 Paso libre

                        // 2. ⚠️ Advertencia visual para Incidencias / Exclusiones
                        if (check && (check.tiene_incidencias || check.tiene_exclusiones)) {
                            const cat = check.categoria ? `[${check.categoria}] ` : '';
                            const det = check.descripcion || '';
                            const textoAlerta = `⚠️ ATENCIÓN CLIENTE: ${cat}${det}`;
                            
                            console.warn("📢 Disparando alerta visual de incidencias:", textoAlerta);

                            if (typeof mostrarToast === "function") {
                                mostrarToast(textoAlerta, "error");
                            } else if (typeof crearToastEmergencia === "function") {
                                crearToastEmergencia(textoAlerta);
                            }
                        }
                    }
                } else {
                    console.warn("⚠️ Error en endpoint de incidencias. Status:", resIncidencias.status);
                    window.semaforoRojo = false;
                }
            } catch (eErr) {
                console.error("❌ Error grave al verificar incidencias:", eErr);
                window.semaforoRojo = false;
            }

            console.log("✅ Validación completa. Siguiente Enter enviará.");
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
// 🛡️ Regla de Oro: Normalizador de Teléfono para Integridad de BD
function normalizarTelefonoVenezolano(textoRaw) {
    if (!textoRaw) return { valido: false, numero: "" };

    // 1. Limpiar todo lo que no sea número (+, -, espacios, parentesis)
    let digitos = textoRaw.replace(/\D/g, "");

    // 2. Corregir formato internacional WhatsApp (+58414... / 58414...)
    if (digitos.startsWith("58")) {
        digitos = "0" + digitos.substring(2);
    }

    // 3. Corregir falta de cero inicial (4143748200 -> 04143748200)
    if (digitos.length === 10 && (digitos.startsWith("4") || digitos.startsWith("2"))) {
        digitos = "0" + digitos;
    }

    // 4. VALIDACIÓN ESTRICTA DE BD (Expresión regular de Venezuela)
    // Debe empezar por 04 (móvil) o 0276 (fijo Táchira) y tener exactamente 11 dígitos
    const regexValido = /^(04\d{9}|0276\d{7})$/;
    
    // Cortamos a 11 por seguridad
    const numeroFinal = digitos.slice(0, 11);
    const esValido = regexValido.test(numeroFinal);

    return {
        valido: esValido,
        numero: numeroFinal
    };
}

// 🎯 Captura en el Pegado (Ctrl+V)
document.addEventListener("paste", function(e) {
    const target = e.target;
    if (target && target.id === "desTelefono") {
        e.preventDefault();
        e.stopPropagation();

        const textoClipboard = (e.clipboardData || window.clipboardData).getData("text");
        const resultado = normalizarTelefonoVenezolano(textoClipboard);

        // Inyectamos SIEMPRE el número transformado y limpio (Ej: 04167739099)
        target.value = resultado.numero;

        if (resultado.valido) {
            console.log(`✅ [INTEGRIDAD OK] Pegado limpio: "${textoClipboard}" ➔ BD: "${resultado.numero}"`);
            
            // Disparar búsqueda del cliente en la BD
            target.dispatchEvent(new Event('input', { bubbles: true }));
            const eventoEnter = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true });
            target.dispatchEvent(eventoEnter);
        } else {
            console.warn(`⚠️ Teléfono inválido tras normalizar: "${resultado.numero}"`);
            if (typeof mostrarToast === 'function') {
                mostrarToast("⚠️ El número debe ser un celular (04...) o fijo (0276...)", "error");
            }
        }
    }
}, true);

// ⚡ Evaluador de estado del formulario Express
function verificarEstadoFormularioExpress() {
    const btnEnviar = document.getElementById("btnEnviarDespacho");
    const tel = document.getElementById("desTelefono")?.value.trim();
    const nom = document.getElementById("desNombre")?.value.trim();
    const ori = document.getElementById("desOrigen")?.value.trim();

    if (!btnEnviar) return;

    // Condición mínima para enviar (sea a despacho directo o a cola):
    // Debe haber un teléfono válido, nombre (distinto de "Buscando...") y dirección de origen.
    const listo = Boolean(tel && nom && nom !== "Buscando..." && ori && ori !== "Buscando...");

    btnEnviar.disabled = !listo;
    if (listo) {
        btnEnviar.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
        btnEnviar.classList.add("opacity-50", "cursor-not-allowed");
    }
}
window.verificarEstadoFormularioExpress = verificarEstadoFormularioExpress;