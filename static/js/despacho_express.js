// ==================== Bloque 1: Flujo rápido (alta demanda) ====================
document.addEventListener("DOMContentLoaded", () => {
    const formDespacho = document.getElementById("formDespacho");
    const telefonoInput = document.getElementById("desTelefono");
    const btnEnviar = document.getElementById("btnEnviarDespacho");

    btnEnviar.disabled = true;

    // Enter en teléfono → validar cliente y saltar foco
    telefonoInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault(); // Evita envío accidental
            validarClientePorTelefono(); 
        }
    });

    // Submit del formulario principal → crear registro en la cola
    formDespacho.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (btnEnviar.disabled) {
            mostrarToast("⚠️ Valida el cliente antes de enviar.", "error");
            return;
        }
        await crearCola();
    });

    // Botón cancelar sección despacho
    document.getElementById("btnCancelarPrincipal")?.addEventListener("click", () => {
        document.getElementById("formDespacho").reset();
        activarCamposDespacho(false);
        document.getElementById("desTelefono").focus();
        mostrarToast("Formulario listo para nueva llamada", "info");
    });
  
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
    // 1. Capturamos los valores (que pueden haber sido editados por el operador)
    const telefono = document.getElementById("desTelefono").value.trim();
    const nombre   = document.getElementById("desNombre").value.trim();
    const origen   = document.getElementById("desOrigen").value.trim();
    const destino  = document.getElementById("desDestino").value.trim();

    // Validación mínima antes de enviar
    if (!telefono || !origen) {
        mostrarToast("⚠️ Teléfono y Origen son obligatorios", "error");
        return;
    }

    const payload = { telefono, nombre, origen, destino };

    try {
        const result = await apiFetch("/cola_despachos/", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (result.error) {
            mostrarToast("❌ Error: " + result.error, "error");
            return;
        }

        mostrarToast("✅ Cliente en espera", "success");

        // 2. LIMPIEZA TOTAL
        document.getElementById("formDespacho").reset();
        
        // Deshabilitar campos y quitar colores de "activo"
        activarCamposDespacho(false);
        
        // 3. FOCO AUTOMÁTICO
        // Fundamental para que el operador atienda la siguiente llamada de inmediato
        document.getElementById("desTelefono").focus();
        
        // 4. ACTUALIZACIÓN SILENCIOSA
        // Si el modal de la cola está abierto en otra pantalla o al fondo, se actualiza
        await cargarColaClientes();

    } catch (err) {
        console.error("Error en crearCola:", err);
        mostrarToast("❌ Error de conexión al crear cola", "error");
    }
}

// ==================== Cola de Clientes (Modal Editable) ====================

async function cargarColaClientes() {
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
            // AJUSTE DE MAPEO: Leemos directamente del objeto 'c'
            // Si tu backend usa una relación, c.cliente?.telefono funcionará como respaldo
            const telefono = c.telefono || (c.cliente ? c.cliente.telefono : "---");
            const nombre   = c.nombre   || (c.cliente ? c.cliente.nombre : "Cliente");
            const origen   = c.origen   || (c.cliente ? c.cliente.direccion : "");
            const destino  = c.destino  || "";

            return `
            <tr class="hover:bg-gray-50 text-sm">
                <td class="border px-2 py-1 text-center">${index + 1}</td> 
                <td class="border px-2 py-1 font-bold">${telefono}</td>
                <td class="border px-2 py-1">${nombre}</td>
                <td class="border px-2 py-1">
                    <input type="text" id="editOrigen_${c.id_cola}" 
                           class="w-full border p-1 rounded bg-yellow-50 focus:bg-white" 
                           value="${origen}">
                </td>
                <td class="border px-2 py-1">
                    <input type="text" id="editDestino_${c.id_cola}" 
                           class="w-full border p-1 rounded bg-blue-50 focus:bg-white" 
                           placeholder="Hacia..." value="${destino}">
                </td>
                <td class="border px-2 py-1">
                    <input type="number" id="tarifaCliente_${c.id_cola}"
                           class="border p-1 w-20 rounded font-bold text-green-700"
                           placeholder="Bs.">
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

        // Guardamos en variables globales para el botón confirmar
        colaSeleccionada = idCola;
        clienteSeleccionado = idCliente;

        // Llenar selects de conductores y autos
        const selectC = document.getElementById("selectConductor");
        const selectA = document.getElementById("selectAuto");
        selectC.innerHTML = "";
        selectA.innerHTML = "";

        data.forEach(item => {
            const c = item.conductor || item;
            const a = item.auto || item;
            const idCond = c.id_conductor || item.id_conductor;
            if (idCond) {
                selectC.innerHTML += `<option value="${idCond}">${c.codigo || 'S/C'} - ${c.nombre || item.nombre}</option>`;
                selectA.innerHTML += `<option value="${a.id_auto || idCond}">${a.nro_placa || "S/P"} (${c.nombre || item.nombre})</option>`;
            }
        });

        // POBLAR EL MODAL CON LOS NUEVOS IDs ÚNICOS (o los que definas)
        const modal = document.getElementById("modalCrearDespacho");
       // 4. Poblar los inputs del modal usando los nuevos IDs de tu HTML
        const inputO = document.getElementById("modalOrigenDespacho");
        const inputD = document.getElementById("modalDestinoDespacho");
        const inputT = document.getElementById("modalTarifaDespacho");
        const inputC = document.getElementById("modalClienteIdDespacho");

        // Asignamos con seguridad
        if (inputO) inputO.value = direccion || "";
        if (inputD) inputD.value = destino || ""; // 'destino' ahora sí llegará aquí
        if (inputT) inputT.value = tarifa || "";
        if (inputC) inputC.value = idCliente || "";
        
        modal.classList.remove("hidden");

    } catch (err) {
        console.error("❌ Error:", err);
        mostrarToast("❌ Error al conectar con el servidor", "error");
    }
}
// Confirmar Despacho Final (Elimina de cola y crea despacho)
document.getElementById("btnConfirmarDespacho").onclick = async () => {
    const btnConfirmar = document.getElementById("btnConfirmarDespacho");
    const modal = document.getElementById("modalCrearDespacho");

    // Capturamos desde los nuevos IDs
    const origenVal  = document.getElementById("modalOrigenDespacho")?.value.trim() || "";
    const destinoVal = document.getElementById("modalDestinoDespacho")?.value.trim() || "";
    const tarifaVal  = document.getElementById("modalTarifaDespacho")?.value.trim() || "";
    const clienteId  = document.getElementById("modalClienteIdDespacho")?.value || "";
    
    // Capturamos selects (estos no cambiaron de ID)
    const conductorId = document.getElementById("selectConductor").value;
    const autoId      = document.getElementById("selectAuto").value;

    console.log("🚀 Payload listo:", { origenVal, destinoVal, tarifaVal });

    if (!origenVal || !tarifaVal) {
        mostrarToast("⚠️ El origen y la tarifa son obligatorios", "error");
        return;
    }

    const payload = {
        // 1. IDs: Convertimos a entero por seguridad
        cliente_id: parseInt(clienteId),
        conductor_id: parseInt(conductorId),
        auto_id: parseInt(autoId),
        
        // 2. Nombres exactos según tu clase Despacho(db.Model)
        origen_despacho: origenVal,    // Antes era 'origen'
        destino_despacho: destinoVal,  // Antes era 'destino'
        
        // 3. Tipos de datos correctos
        tarifa: parseFloat(tarifaVal), // El modelo dice db.Float
        estado_despacho: "en curso",   // El modelo dice db.String(50)
        
        // Si tu servidor procesa la cola_id manualmente, déjalo, 
        // pero recuerda que no está definido en el modelo que pasaste
        cola_id: parseInt(colaSeleccionada) 
    };

    try {
        btnConfirmar.disabled = true;
        btnConfirmar.innerText = "Procesando...";

        const response = await apiFetch("/despachos/", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            mostrarToast(`✅ Despacho creado con éxito`, "success");
            modal.classList.add("hidden");
            await cargarColaClientes(); 
        } else {
            const errorData = await response.json();
            mostrarToast("❌ Error: " + (errorData.error || "Datos incompletos"), "error");
        }
    } catch (err) {
        console.error("Error en Despacho:", err);
        mostrarToast("❌ Error de conexión", "error");
    } finally {
        btnConfirmar.disabled = false;
        btnConfirmar.innerText = "Confirmar Despacho";
    }
};/**
 * Función mejorada para validar y mover foco al botón Enviar
 */
async function validarClientePorTelefono() {
    const telInput = document.getElementById('desTelefono');
    const tel = telInput.value.trim();
    if (!tel) return;

    const res = await apiFetch(`/clientes/buscar?telefono=${tel}`);
    const cliente = (res && res.length > 0) ? res[0] : null;

    if (cliente) {
        document.getElementById('desNombre').value = cliente.nombre;
        document.getElementById('desOrigen').value = cliente.direccion;
        activarCamposDespacho(true);
        
        // FOCO RÁPIDO: Salto al botón enviar para procesar con un segundo Enter
        setTimeout(() => document.getElementById("btnEnviarDespacho").focus(), 100);
    } else {
        activarCamposDespacho(false);
        abrirModalCliente(tel, null); // Abrir modal para crear cliente nuevo
    }
}

function activarCamposDespacho(activar) {
    const campos = ["desNombre", "desOrigen", "desDestino", "btnEnviarDespacho"];
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
