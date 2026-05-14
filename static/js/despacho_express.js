// ==================== Bloque 1: Flujo rápido (alta demanda) ====================
let memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} };
document.addEventListener("DOMContentLoaded", () => {
    const formDespacho = document.getElementById("formDespacho");
    const telefonoInput = document.getElementById("desTelefono");
    const btnEnviar = document.getElementById("btnEnviarDespacho");

    if (btnEnviar) btnEnviar.disabled = true;

   // 1️⃣ EVENTO DE TELÉFONO ULTRA-CONTROLADO
    // 2️⃣ EVENTO DE TECLADO ULTRA-CONTROLADO
    // 1. EL SEMÁFORO (Ponlo arriba del todo, fuera del addEventListener)
    // Variable global para el Semáforo (fuera del listener)
    let clienteListoParaEnviar = null; 

    telefonoInput?.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            event.stopImmediatePropagation();

            // 1️⃣ VALIDACIÓN NATIVA (Si el número está incompleto, se frena aquí)
            if (!telefonoInput.checkValidity()) {
                mostrarToast("⚠️ " + telefonoInput.validationMessage, "error");
                telefonoInput.reportValidity();
                return; 
            }

            // 🚩 RESETEAR EL SEMÁFORO AQUÍ 
            // Esto asegura que si el operador cambió el número a mitad de camino, 
            // el sistema no intente un envío directo con datos viejos.
            const telActual = telefonoInput.value.trim();

            const inputNom = document.getElementById("desNombre");
            const inputOri = document.getElementById("desOrigen");
            const inputDes = document.getElementById("desDestino");
            const btnEnv = document.getElementById("btnEnviarDespacho");

            // 🎯 PASO 2: EL SEGUNDO ENTER (ENVÍO DIRECTO)
            // Solo entra aquí si el semáforo coincide con el teléfono que está en el input
            if (clienteListoParaEnviar === telActual && inputNom && inputNom.value.trim() !== "") {
                console.log("🚀 SEMÁFORO VERDE: Enviando despacho...");
                if (btnEnv) {
                    btnEnv.disabled = false;
                    btnEnv.click();
                }
                clienteListoParaEnviar = null; 
                return;
            }

            // 🎯 PASO 1: EL PRIMER ENTER (VALIDACIÓN E INCIDENCIAS)
            console.log("⌨️ SEMÁFORO ROJO: Preparando nueva validación...");
            
            // Limpiamos la memoria del semáforo antes de buscar para evitar "fantasmas"
            clienteListoParaEnviar = null; 

            // Feedback visual inmediato para el operador
            if (inputNom) inputNom.value = "Buscando..."; 
            if (inputOri) inputOri.value = "Buscando..."; 
            if (inputDes) inputDes.value = ""; 

            const resultado = await validarClienteExpreso();
            
            if (resultado && resultado.valido === true && resultado.cliente) {
                const c = resultado.cliente;
                
                // ✅ Llenar campos y bloquear
                if (inputNom) {
                    inputNom.value = c.nombre || "";
                    inputNom.readOnly = true;
                    inputNom.style.backgroundColor = "#f3f4f6"; 
                }
                if (inputOri) {
                    inputOri.value = c.direccion || "";
                    inputOri.readOnly = true;
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
                    inputDes.focus(); // Mover foco al destino
                }
                 clienteListoParaEnviar = telActual; 
                if (btnEnv) btnEnv.disabled = false;
                
                console.log("✅ Validación completa. Siguiente Enter enviará.");
                const idParaIncidencia = c.id_cliente || c.cliente_id || c.id;
                if (idParaIncidencia) { // <--- Usamos la variable recién declarada
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
                            else if (check.tiene_exclusiones === true) {
                                // 🧠 Ahora sí es 100% DINÁMICO:
                                const catReal = check.categoria || "INCIDENCIA"; // Traído del nuevo campo en Flask
                                const descReal = check.descripcion || "Sin descripción";

                                // Mostrará "EXCESO_CARGA: más de cinco" o "GROSERIAS: habló con groserías"
                                crearToastEmergencia(`⚠️ ${catReal}: ${descReal}`);
                            }
                        }
                    } catch (err) {
                        console.error("❌ Error en incidencias:", err);
                    }
                }

                // ✅ PREPARAR SEMÁFORO PARA EL SIGUIENTE ENTER
                // Si todo salió bien, ahora sí autorizamos el envío directo en el próximo Enter
                //clienteListoParaEnviar = telActual; 
                //if (btnEnv) btnEnv.disabled = false;
                
                //console.log("✅ Validación completa. Siguiente Enter enviará.");

            } else {
                // 🆕 CLIENTE NUEVO: Abrir modal
                console.log("🆕 Cliente no encontrado.");
                if (typeof abrirModalCliente === 'function') {
                    abrirModalCliente(telActual, null);
                }
            }
        }
    });
    // Submit del formulario principal → crear registro en la cola
    formDespacho?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (btnEnviar && btnEnviar.disabled) {
            mostrarToast("⚠️ Valida el cliente antes de enviar.", "error");
            return;
        }
        await crearCola();
    });

    // Botón cancelar sección despacho
    document.getElementById("btnCancelarPrincipal")?.addEventListener("click", () => {
        // 1. Limpiar lo visual
        document.getElementById("formDespacho").reset();
        
        // 2. 🔥 LIMPIAR EL CEREBRO (Esto es lo que faltaba)
        // Borramos cualquier dato temporal de la cola rápida
        memoriaEdicionCola1 = { origenes: {}, destinos: {}, tarifas: {} }; 
        
        // Matamos el semáforo para que la próxima búsqueda sea "desde cero"
        clienteListoParaEnviar = null; 

        // 3. Bloquear campos y dar foco
        activarCamposDespacho(false);
        
        // Si tiene campos de lectura (readonly), quítele el color gris
        const inputNom = document.getElementById("desNombre");
        if (inputNom) {
            inputNom.readOnly = false;
            inputNom.style.backgroundColor = "#ffffff";
        }

        document.getElementById("desTelefono").focus();
        
        // Un mensaje que le confirme al operador que TODO se limpió
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
  // Listener de teclado global
  document.addEventListener("keydown", (event) => {
      // Si presionas Alt + C (o Alt + c)
      if (event.altKey && (event.key.toLowerCase() === "c" || event.code === "KeyC")) {
          event.preventDefault(); // Evita que el navegador use el atajo para otra cosa
          abrirModalCola(); // Ejecuta la función
      }
  });
    function abrirModalCola() {
        console.log("⚡ abrirModalCola ejecutado desde despachos_express.js");
        const modalCola = document.getElementById("modalColaClientes");
        modalCola.classList.remove("hidden");
        cargarColaClientes(); // refresca tabla al abrir
        //refrescarConductoresDisponibles();
    }

    function cerrarModalCola() {
        const modalCola = document.getElementById("modalColaClientes");
        modalCola.classList.add("hidden");
    }

// Listener para botón cerrar modal
const btnCerrarCola = document.getElementById("btnCerrarCola");
if (btnCerrarCola) {
  btnCerrarCola.addEventListener("click", cerrarModalCola);
}
// Función: Crear entrada en la cola (con origen y destino editable)

async function crearCola() {
    const telefono = document.getElementById("desTelefono").value.trim();
    const nombre   = document.getElementById("desNombre").value.trim();
    const origen   = document.getElementById("desOrigen").value.trim();
    const destino  = document.getElementById("desDestino").value.trim();
    
    // CAPTURAMOS LA CANTIDAD DESDE EL SELECT
    const tipoValor = document.getElementById("tipoDespacho").value;
    
    // Si es "reserva", no procesamos aquí (este es el flujo express)
    if (tipoValor === "reserva") return;
    
    // Convertimos a número si es 2, 3 o 4. Si no, la cantidad es 1.
    const cantidad = (['2', '3', '4'].includes(tipoValor)) ? parseInt(tipoValor) : 1;

    if (!telefono || !origen) {
        mostrarToast("⚠️ Teléfono y Origen son obligatorios", "error");
        return;
    }

    // Usaremos un bucle para enviar la cantidad de autos solicitada
    try {
        let errores = 0;
        
        for (let i = 0; i < cantidad; i++) {
            // Si son varios, añadimos una nota automática para el despachador
            const notaGrupo = cantidad > 1 ? ` (Auto ${i + 1} de ${cantidad})` : "";
            
            const payload = { 
                telefono, 
                nombre, 
                origen, 
                destino: destino + notaGrupo 
            };

            const result = await apiFetch("/cola_despachos/", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (result.error) errores++;
        }

        if (errores > 0) {
            mostrarToast(`❌ Hubo errores en ${errores} registros`, "error");
        } else {
            mostrarToast(cantidad > 1 ? `✅ ${cantidad} unidades en espera` : "✅ Cliente en espera", "success");
        }

        // LIMPIEZA Y REINICIO (Igual que antes)
        document.getElementById("formDespacho").reset();
        activarCamposDespacho(false);
        document.getElementById("desTelefono").focus();
        
        await cargarColaClientes();

    } catch (err) {
        console.error("Error en crearCola múltiple:", err);
        mostrarToast("❌ Error de conexión al crear cola", "error");
    }
}

// ==================== Cola de Clientes (Modal Editable) ====================
// Memoria temporal para no perder lo que el operador escribe en la tabla
let memoriaEdicionCola = {
    origenes: {},
    destinos: {},
    tarifas: {}
};
async function cargarColaClientes() {
    // 🧹 LIMPIEZA DE MEMORIA FANTASMA
    memoriaEdicionCola1.origenes = {};
    memoriaEdicionCola1.destinos = {};
    memoriaEdicionCola1.tarifas = {};
    const tbodyCola = document.getElementById("tablaColaClientes");
    if (!tbodyCola) return;

    tbodyCola.innerHTML = `<tr><td colspan="8" class="text-center">Cargando...</td></tr>`;

    try {
        const res = await apiFetch("/cola_despachos/");
        
        // --- CORRECCIÓN AQUÍ ---
        // Si res es un objeto Response, necesitamos sacar el JSON
        let data;
        if (res && typeof res.json === 'function') {
            data = await res.json();
        } else {
            data = res; // Si ya era JSON, lo dejamos igual
        }
        // ------------------------

        if (!Array.isArray(data) || data.length === 0) {
            tbodyCola.innerHTML = `<tr><td colspan="8" class="text-center py-4">No hay clientes en espera</td></tr>`;
            return;
        }

        tbodyCola.innerHTML = data.map((c, index) => {
            const id = c.id_cola;
            const telefono = c.telefono || (c.cliente ? c.cliente.telefono : "---");
            const nombre = c.nombre || (c.cliente ? c.cliente.nombre : "Cliente");
            const origen = c.origen || (c.cliente ? c.cliente.direccion : "");
            const destino = c.destino || "";

            const grupo = data.filter(item => {
                const telItem = (item.telefono || item.cliente?.telefono || "").toString().trim();
                const telActual = telefono.toString().trim();
                return telItem === telActual && telActual !== "";
            });

            const totalAutos = grupo.length;
            let placeholderTexto = "Hacia...";
            if (totalAutos > 1) {
                const posicion = grupo.findIndex(item => item.id_cola === id) + 1;
                placeholderTexto = `Auto ${posicion} de ${totalAutos}...`;
            }

            const valOrigen = memoriaEdicionCola1.origenes[id] || origen;
            const valDestino = memoriaEdicionCola1.destinos[id] || destino;
            const valTarifa = memoriaEdicionCola1.tarifas[id] || "";

            // --- LÓGICA DE LIMPIEZA MANTENIDA ---
            const destinoLimpio = (destino.includes("(Auto") || !destino.trim()) ? "" : destino.trim();
            let valorFinalDestino = (valDestino.includes("(Auto") || !valDestino.trim()) ? destinoLimpio : valDestino.trim();
            if (valorFinalDestino.includes("Auto")) valorFinalDestino = "";

            // --- INTEGRACIÓN INTELIGENTE DE MATRIZ DE TARIFAS ---
            // Esta cadena se ejecuta cada vez que el operador escribe en el destino
            // Este bloque va dentro del mapa de filas de cargarColaClientes
            const onInputDestino = `
                const val = this.value;
                // Buscamos si lo que escribió el usuario es EXACTAMENTE un destino de la lista
                const tarifaMatch = MATRIZ_TARIFAS.find(t => t.destino === val);
                
                if (tarifaMatch) {
                    // Si lo encuentra, actualiza el precio en pantalla y en la memoria del formulario
                    const monto = tarifaMatch.precio_cop;
                    memoriaEdicionCola1.tarifas[${id}] = monto;
                    
                    const inputTarifa = document.getElementById('tarifaCliente_${id}');
                    if(inputTarifa) {
                        inputTarifa.value = monto;
                        // Un pequeño efecto visual para que el operador note el cambio
                        inputTarifa.classList.add('bg-green-100');
                        setTimeout(() => inputTarifa.classList.remove('bg-green-100'), 500);
                    }
                }
                // Guardamos la dirección completa (con detalles extra si los hay)
                memoriaEdicionCola1.destinos[${id}] = val;
            `;
            return `
            <tr class="hover:bg-gray-50 text-sm">
                <td class="border px-2 py-1 text-center">${index + 1}</td> 
                <td class="border px-2 py-1 font-bold">${telefono}</td>
                <td class="border px-2 py-1">${nombre}</td>
                <td class="border px-2 py-1">
                    <input type="text" id="editOrigen_${id}" 
                        class="w-full border p-1 rounded bg-yellow-50 focus:bg-white" 
                        value="${valOrigen}"
                        oninput="memoriaEdicionCola1.origenes[${id}] = this.value">
                </td>
                <td class="border px-2 py-1">
                    <input type="text" id="editDestino_${id}" 
                        list="listaTarifasMatriz" 
                        class="w-full border p-1 rounded bg-blue-50 focus:bg-white" 
                        placeholder="${placeholderTexto}" 
                        value="${valorFinalDestino}" 
                        onfocus="this.select()"
                        oninput="${onInputDestino}">
                </td>
                <td class="border px-2 py-1">
                    <input type="number" id="tarifaCliente_${id}"
                        class="border p-1 w-20 rounded font-bold text-green-700"
                        placeholder="COP"
                        value="${valTarifa}"
                        oninput="memoriaEdicionCola1.tarifas[${id}] = this.value">
                </td>
                <td class="border px-2 py-1 text-center">
                    <span class="px-2 py-1 rounded bg-orange-100 text-xs text-orange-700 font-semibold">${c.estado}</span>
                </td>
                <td class="border px-2 py-1 flex gap-1 justify-center">
                    <button onclick="prepararAsignacion(${c.id_cola}, ${c.cliente?.id_cliente || c.id_cliente})"
                            class="bg-blue-600 text-white px-2 py-1 rounded">
                        Asignar
                    </button>
                    <button onclick="cancelarCliente(${c.id_cola})"
                            class="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 text-xs">×</button>
                </td>
            </tr>`;
        }).join("");

    } catch (err) {
        console.error("Error al cargar la cola:", err);
        tbodyCola.innerHTML = `<tr><td colspan="8" class="text-center text-red-500">Error de conexión</td></tr>`;
    }
    actualizarContadorConductores(); // Actualiza el número al abrir
}
// ==================== Modal de Asignación Final ====================
function prepararAsignacion(idCola, idCliente) {
    // 1. Capturamos los valores actuales de la fila en la tabla
    const origenDinamico = document.getElementById(`editOrigen_${idCola}`)?.value || "";
    const destinoDinamico = document.getElementById(`editDestino_${idCola}`)?.value || "";
    const tarifaDinamica = document.getElementById(`tarifaCliente_${idCola}`)?.value || "";

    console.log("📍 Captura desde Tabla:", { origenDinamico, destinoDinamico, tarifaDinamica });

    // 2. Pasamos TODO a la función que abre el modal
    abrirModalDespacho(idCola, idCliente, origenDinamico, destinoDinamico, tarifaDinamica);
}
async function abrirModalDespacho(idCola, idCliente, direccion, destino, tarifa) {
    console.log("📝 Preparando modal para cliente:", idCliente);
    
    // Validación de Tarifa antes de seguir
    if (!tarifa) {
        mostrarToast("⚠️ Indica la tarifa en la tabla antes de asignar", "error");
        return;
    }

    try {
        const res = await apiFetch("/conductores/en_turno_disponibles");
        const data = (res && typeof res.json === 'function') ? await res.json() : res;

        if (!Array.isArray(data) || data.length === 0) {
            mostrarToast("🚫 No hay conductores disponibles", "error");
            return;
        }

        const selectC = document.getElementById("selectConductor");
        const selectA = document.getElementById("selectAuto");
        selectC.innerHTML = "";
        selectA.innerHTML = "";

        // 1. Llenamos los selects
        data.forEach(item => {
            const c = item.conductor || item;
            const a = item.auto || item;
            const idCond = c.id_conductor || item.id_conductor;
            const idAuto = a.id_auto || idCond;

            if (idCond) {
                // El value del conductor será su ID
                selectC.innerHTML += `<option value="${idCond}">${c.codigo || 'S/C'} - ${c.nombre}</option>`;
                // El value del auto será su ID
                selectA.innerHTML += `<option value="${idAuto}">${a.nro_placa || "S/P"} (${c.nombre})</option>`;
            }
        });

        // 2. ⚡ VINCULACIÓN AUTOMÁTICA
        selectC.onchange = function() {
            const idSeleccionado = parseInt(this.value);
            // Buscamos en 'data' el objeto que coincida con el conductor elegido
            const relacion = data.find(item => (item.conductor?.id_conductor || item.id_conductor) === idSeleccionado);
            
            if (relacion) {
                const auto = relacion.auto || relacion;
                selectA.value = auto.id_auto || idSeleccionado;
                
                // Feedback visual: resaltar el auto seleccionado
                selectA.classList.add("bg-green-100");
                setTimeout(() => selectA.classList.remove("bg-green-100"), 500);
            }
        };

        // ... resto de tu lógica de poblar inputs y mostrar modal ...
        // 3. ASIGNACIÓN DE VALORES A LOS INPUTS DEL MODAL
        // Aquí pasamos lo que llega por parámetros a los inputs que están en el HTML
        document.getElementById("modalClienteIdDespacho").value = idCliente || "";
        document.getElementById("modalOrigenDespacho").value    = direccion || "";
        document.getElementById("modalDestinoDespacho").value   = destino   || "";
        document.getElementById("modalTarifaDespacho").value    = tarifa    || "";
        
        // Guardamos la cola seleccionada en una variable global (para que el botón "Confirmar" la use)
        window.colaSeleccionada = idCola; 

        // 4. Mostrar el modal
        const modal = document.getElementById("modalCrearDespacho");
        modal.classList.remove("hidden");
    } catch (err) {
        console.error("❌ Error:", err);
    }
}
// Confirmar Despacho Final (Elimina de cola, valida exclusión y crea despacho)
document.getElementById("btnConfirmarDespacho").onclick = async () => {
    const btnConfirmar = document.getElementById("btnConfirmarDespacho");
    const modal = document.getElementById("modalCrearDespacho");

    // Capturamos valores
    const origenVal  = document.getElementById("modalOrigenDespacho")?.value.trim() || "";
    const destinoVal = document.getElementById("modalDestinoDespacho")?.value.trim() || "";
    const tarifaVal  = document.getElementById("modalTarifaDespacho")?.value.trim() || "";
    const clienteId  = document.getElementById("modalClienteIdDespacho")?.value || "";
    
    const conductorId = document.getElementById("selectConductor").value;
    const autoId      = document.getElementById("selectAuto").value;

    if (!origenVal || !tarifaVal) {
        mostrarToast("⚠️ El origen y la tarifa son obligatorios", "error");
        return;
    }

    if (!clienteId || !conductorId) {
        mostrarToast("⚠️ Datos de cliente o conductor incompletos", "error");
        return;
    }

    try {
        btnConfirmar.disabled = true;
        btnConfirmar.innerText = "Validando...";

        // ====================================================================
        // 🚨 PASO NUEVO: Validar exclusión mutua (Escenario B)
        // ====================================================================
        const checkAfinidad = await apiFetch("/incidencias/validar_afinidad", {
            method: "POST",
            body: JSON.stringify({
                cliente_id: parseInt(clienteId),
                conductor_id: parseInt(conductorId)
            })
        });

        // Verificamos si existe un bloqueo activo
        if (checkAfinidad && checkAfinidad.permitido === false) {
            mostrarToast(checkAfinidad.mensaje, "error");
            btnConfirmar.disabled = false;
            btnConfirmar.innerText = "Confirmar Despacho";
            return; // 🛑 Detiene la creación del despacho
        }
        // ====================================================================

        btnConfirmar.innerText = "Procesando...";

        const payload = {
            cliente_id: parseInt(clienteId),
            conductor_id: parseInt(conductorId),
            auto_id: parseInt(autoId),
            origen_despacho: origenVal,
            destino_despacho: destinoVal,
            tarifa: parseFloat(tarifaVal),
            estado_despacho: "en curso",
            cola_id: parseInt(colaSeleccionada) 
        };

        const result = await apiFetch("/despachos/", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (result && !result.error) {
            mostrarToast(`✅ Despacho creado con éxito`, "success");
            modal.classList.add("hidden");

            // Limpiar memoria
            memoriaEdicionCola1.destinos = {}; 
            delete memoriaEdicionCola1.origenes[colaSeleccionada];
            // ... (restante de su limpieza)

            // 🚀 MEJORA: Refrescar en paralelo. No usamos 'await' secuencial.
            console.log("🔄 Iniciando refresco paralelo...");
            Promise.all([
                cargarColaClientes(),
                typeof refrescarConductoresDisponibles === 'function' ? refrescarConductoresDisponibles() : Promise.resolve()
            ]).then(() => {
                console.log("✅ Sistema actualizado completamente");
            });
        } else {
            mostrarToast("❌ Error: " + (result.error || "No se pudo crear el despacho"), "error");
        }
    } catch (err) {
        console.error("❌ Error en Despacho:", err);
        mostrarToast("❌ Error de conexión o del servidor", "error");
    } finally {
        btnConfirmar.disabled = false;
        btnConfirmar.innerText = "Confirmar Despacho";
    }
};
/**
 * Función mejorada para validar y mover foco al botón Enviar
 */
let motivoSuspensionGlobal = "";


// Función de validación (la dejamos simple como respaldo)
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

        // Fetch nativo directo a la URL
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
            if (document.getElementById('desOrigen')) document.getElementById('desOrigen').value = cliente.direccion || "";
            
            // Retornamos el objeto cliente explícitamente
            return { valido: true, cliente: cliente };
        }

        return { valido: false, motivo: "Cliente no registrado" };

    } catch (err) {
        console.error("❌ Error grave en validarClienteExpreso:", err);
        return { valido: false, motivo: "Error de conexión" };
    }
}

// 📌 FUNCIÓN PARA EL TOAST ROJO
function crearToastEmergencia(mensaje, tipo = "VETO") { // Añadimos tipo opcional
    const alertaPrevia = document.getElementById("toast-emergencia");
    if (alertaPrevia) alertaPrevia.remove();

    const div = document.createElement("div");
    div.id = "toast-emergencia";
    
    // 🎯 CAMBIO AQUÍ: Ahora usará el mensaje que construimos en el bloque de incidencias
    div.innerText = mensaje; 
    
    Object.assign(div.style, {
        position: "fixed",
        top: "20px",
        right: "20px",
        backgroundColor: "#ef4444", // Rojo para que resalte
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
    const campos = ["desNombre", "desOrigen", "desDestino", "btnEnviarDespacho", "btnModificarCliente"];
    campos.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.disabled = !activar;
            el.classList.toggle("bg-gray-100", !activar);
            el.classList.toggle("cursor-not-allowed", !activar);
        }
    });
}

async function cancelarCliente(idCola) {
    // Preguntamos para evitar borrar por error
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
            // Refrescamos la tabla para que desaparezca la fila
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
            // Cambia color según disponibilidad
            badge.className = totalDisponibles > 0 
                ? "bg-green-100 text-green-800 text-xs font-bold px-2.5 py-1 rounded border border-green-500"
                : "bg-red-100 text-red-800 text-xs font-bold px-2.5 py-1 rounded border border-red-500";
        }
    } catch (error) {
        console.error("Error al contar conductores:", error);
    }
}

function generarDatalistTarifas() {
    let html = '<datalist id="listaTarifasMatriz">';
    MATRIZ_TARIFAS.forEach(t => {
        html += `<option value="${t.destino}">${t.municipio} - ${t.precio} COP</option>`;
    });
    html += '</datalist>';
    // Lo inyectamos al final del body si no existe
    if (!document.getElementById("listaTarifasMatriz")) {
        document.body.insertAdjacentHTML('beforeend', html);
    }
}
generarDatalistTarifas();

function actualizarPrecio(input, idFila) {
    const destinoSeleccionado = input.value;
    // Buscamos en la matriz que cargaste desde Flask
    const datos = MATRIZ_TARIFAS.find(t => t.destino === destinoSeleccionado);
    
    if (datos) {
        const inputPrecio = document.getElementById(`tarifa_${idFila}`);
        inputPrecio.value = datos.precio_cop;
        console.log(`💰 Precio actualizado para ${datos.destino}: ${datos.precio_cop} COP`);
    }
}
