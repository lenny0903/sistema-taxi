// ==================== Módulo: Despacho Múltiple (despacho_multiple.js) ====================

document.addEventListener("DOMContentLoaded", () => {
    const selectTipoDespacho = document.getElementById("tipoDespacho");
    const inputDestino = document.getElementById("desDestino");
    const tarifaInput = document.getElementById("tarifaClienteUnico");
    const inputOrigen = document.getElementById("desOrigen");

    if (!selectTipoDespacho) return;

    // 🎯 1. Detectar cambio en el tipo de despacho
    selectTipoDespacho.addEventListener("change", (e) => {
        const valor = e.target.value;

        if (valor.includes("_dif")) {
            if (inputDestino) {
                inputDestino.disabled = false;
                inputDestino.value = "";
                inputDestino.focus();
            }
            if (tarifaInput) {
                tarifaInput.value = "";
                tarifaInput.disabled = false;
            }
            if (typeof mostrarToast === "function") {
                mostrarToast("🔀 Modo Múltiple: Diferentes destinos activado.", "info");
            }
        } else if (valor.includes("_mismo")) {
            if (inputDestino) {
                inputDestino.disabled = false;
                inputDestino.value = "";
                inputDestino.focus();
            }
            if (tarifaInput) {
                tarifaInput.disabled = false;
                tarifaInput.value = "";
            }
        }
    });

    // ⌨️ 2. DISPARAR ENTER EN DESTINO EXCLUSIVAMENTE PARA "DIFERENTES DESTINOS" (_dif)
    document.addEventListener("keydown", async (e) => {
        if (e.key === "Enter" && e.target && e.target.id === "desDestino") {
            const tipoModalidad = selectTipoDespacho.value;

            // Solo actuamos si es _dif y NO estamos en modo de edición/asignación individual
            if (tipoModalidad && tipoModalidad.includes("_dif") && !window.idColaEnEdicion) {
                e.preventDefault();
                e.stopImmediatePropagation();

                const clienteId = document.getElementById("modalClienteIdDespacho")?.value;
                const telefono = document.getElementById("desTelefono")?.value.trim();
                const nombre = document.getElementById("desNombre")?.value.trim();
                const origen = inputOrigen ? inputOrigen.value.trim() : "";

                if (!telefono || !origen) {
                    if (typeof mostrarToast === "function") {
                        mostrarToast("⚠️ Faltan datos obligatorios (Teléfono u Origen).", "warning");
                    }
                    return;
                }

                const formDataCliente = {
                    cliente_id: clienteId ? parseInt(clienteId) : null,
                    telefono,
                    nombre,
                    origen,
                    destino: "", // Vacío para que se edite en la cola
                    tarifa: 0
                };

                console.log("🚀 Enter en Destino (Diferentes Destinos). Creando cola múltiple...");
                await window.procesarDespachoMultiple(formDataCliente, tipoModalidad);
            }
        }
    }, true);
});

/**
 * 🚀 Función para procesar y enviar lotes múltiples a la cola de espera
 */
window.procesarDespachoMultiple = async function(formDataCliente, tipoModalidad) {
    const cantidadVehiculos = parseInt(tipoModalidad.charAt(0)) || 2;
    const esMismoDestino = tipoModalidad.includes("_mismo");

    // 🎯 Capturamos el valor REAL actual de los inputs de la interfaz una sola vez antes del bucle
    const inputDestinoElem = document.getElementById("desDestino");
    const inputTarifaElem = document.getElementById("tarifaClienteUnico");
    
    const destinoCapturado = inputDestinoElem ? inputDestinoElem.value.trim() : "";
    const tarifaCapturada = inputTarifaElem ? parseFloat(inputTarifaElem.value) || 0 : 0;

    console.log(`📦 Procesando despacho múltiple: ${cantidadVehiculos} vehículos (${esMismoDestino ? 'Mismo destino' : 'Diferentes destinos'})`);

    try {
        for (let i = 1; i <= cantidadVehiculos; i++) {
            let destinoFinal = "";
            let tarifaFinal = 0;
            let estadoFinal = "PENDIENTE";

            if (esMismoDestino) {
                // Si es mismo destino, TODAS las unidades llevan el mismo destino capturado y la nota de caravana
                destinoFinal = destinoCapturado; 
                tarifaFinal = tarifaCapturada;
                estadoFinal = "Múltiple (Mismo Dst)";
            } else {
                // Si es diferente destino, van vacíos para llenarse individualmente en la tabla
                destinoFinal = "";
                tarifaFinal = 0;
                estadoFinal = "PENDIENTE";
            }

            const payloadCola = {
                cliente_id: formDataCliente.cliente_id,
                telefono: formDataCliente.telefono,
                nombre: `${formDataCliente.nombre} [Unidad ${i}/${cantidadVehiculos}]`,
                origen: formDataCliente.origen,
                destino: destinoFinal,
                tarifa: tarifaFinal,
                estado: estadoFinal
            };
            console.log("🚀 Payload enviado al backend:", payloadCola);
            await apiFetch("/cola_despachos/", {
                method: "POST",
                body: JSON.stringify(payloadCola)
            });
        }

        if (typeof mostrarToast === "function") {
            mostrarToast(`✅ Cola múltiple de ${cantidadVehiculos} vehículos creada con éxito`, "success");
        }

        // Restablecer select y limpiar inputs
        const selectTipo = document.getElementById("tipoDespacho");
        if (selectTipo) selectTipo.selectedIndex = 0;

        if (inputDestinoElem) { inputDestinoElem.value = ""; inputDestinoElem.disabled = false; }
        if (inputTarifaElem) { inputTarifaElem.value = ""; inputTarifaElem.disabled = false; }

        if (typeof cargarColaClientes === "function") {
            cargarColaClientes();
        }

        return true;
    } catch (err) {
        console.error("❌ Error al crear despacho múltiple:", err);
        if (typeof mostrarToast === "function") {
            mostrarToast("❌ Error al registrar la cola múltiple", "error");
        }
        return false;
    }
};