// ==================== Bloque 1: Flujo rápido (alta demanda) ====================
document.addEventListener("DOMContentLoaded", () => {
  const formDespacho = document.getElementById("formDespacho");
  const telefonoInput = document.getElementById("desTelefono");
  const btnEnviar = document.getElementById("btnEnviarDespacho");

  // Estado inicial
  btnEnviar.disabled = true;

  // Submit → crear cola
  formDespacho.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (btnEnviar.disabled) {
      alert("⚠️ Primero valida o crea el cliente antes de enviar.");
      return;
    }
    await crearCola(); // ✅ flujo rápido
  });

  // Enter en teléfono → validar cliente
  telefonoInput.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      validarClientePorTelefono();
    }
  });

  // Refrescar cola cuando se edita cliente
  document.addEventListener("clienteActualizado", () => {
    cargarColaClientes();
  });
  
});

// Función auxiliar: crear cola
async function crearCola() {
  const telefono = document.getElementById("desTelefono").value.trim();
  const nombre = document.getElementById("desNombre").value.trim();
  const origen = document.getElementById("desOrigen").value.trim();
  const tipo = document.getElementById("tipoDespacho").value;

  let nro_autos = 1;
  if (tipo && !isNaN(tipo)) nro_autos = parseInt(tipo);

  const payload = { telefono, nombre, origen, nro_autos };

  try {
    const result = await apiFetch("/cola_despachos/", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    if (result.error) {
      mostrarToast("❌ Error: " + result.error, "error");
      return;
    }

    // ✅ apiFetch ya devuelve JSON, no necesitas res.json()
    mostrarToast("✅ Cliente agregado a la cola", "success");

    document.getElementById("formDespacho").reset();
    activarCamposDespacho(false);

    // 🔎 refrescar datos en segundo plano, sin abrir modal
    await cargarColaClientes();
  } catch (err) {
    console.error("❌ Error enviando despacho:", err);
    mostrarToast("❌ Error de conexión al crear cola", "error");
  }
}


// ==================== Cola de Clientes ====================

// Abrir modal con Alt+C
document.addEventListener("keydown", (event) => {
  if (event.altKey && event.key.toLowerCase() === "c") {
    event.preventDefault();
    abrirModalCola();
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

// Cargar clientes en la cola
async function cargarColaClientes() {
  console.log("⚡ cargarColaClientes ejecutado");
  const tbodyCola = document.getElementById("tablaColaClientes");
  tbodyCola.innerHTML = `<tr><td colspan="7">Cargando...</td></tr>`;

  try {
    const token = localStorage.getItem("token");
    console.log("🔑 Token leído:", token);

    const res = await fetch("http://127.0.0.1:5000/cola_despachos/", {
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      }
    });

    if (!res.ok) {
      tbodyCola.innerHTML = `<tr><td colspan="7">Error HTTP ${res.status} al cargar cola</td></tr>`;
      return;
    }

const data = await res.json();

    console.log("📡 Cola recibida:", data);

    if (!Array.isArray(data) || data.length === 0) {
      tbodyCola.innerHTML = `<tr><td colspan="7" class="text-center">No hay clientes en cola</td></tr>`;
      return;
    }

   tbodyCola.innerHTML = data.map((c, index) => `
     <tr>
        <td class="border px-2 py-1">${index + 1}</td> 
        <td class="border px-2 py-1">${c.cliente?.telefono || ""}</td>
        <td class="border px-2 py-1">${c.cliente?.nombre || ""}</td>
        <td class="border px-2 py-1">${c.cliente?.direccion || ""}</td>
        <td class="border px-2 py-1">${c.nro_autos}</td>
        <td class="border px-2 py-1">
          <input type="number" id="tarifaCliente_${c.id_cola}"
                class="border p-1 w-24 rounded"
                placeholder="Bs." min="0">
        </td>
        <td class="border px-2 py-1">${c.estado}</td>
        <td class="border px-2 py-1">
          <button onclick="abrirModalDespacho(${c.id_cola}, ${c.cliente?.id_cliente}, '${c.cliente?.direccion || ""}')"
                  class="bg-blue-600 text-white px-2 py-1 rounded">Asignar</button>
          <button onclick="cancelarCliente(${c.id_cola})"
                  class="bg-red-600 text-white px-2 py-1 rounded">Cancelar</button>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    console.error("❌ Error cargando cola:", err);
    tbodyCola.innerHTML = `<tr><td colspan="7">Error cargando cola</td></tr>`;
  }
}

// Cancelar cliente de la cola
async function cancelarCliente(idCola) {
  try {
    const token = localStorage.getItem("token");
    const res = await fetch(`http://127.0.0.1:5000/cola_despachos/${idCola}`, {
      method: "DELETE",
      headers: {
        "Authorization": "Bearer " + token
      }
    });

    if (!res.ok) {
      const error = await res.json();
      mostrarToast("❌ Error al cancelar cliente: " + (error.error || res.status), "error");
      return;
    }

    mostrarToast("✅ Cliente cancelado de la cola", "success");
    await cargarColaClientes(); // refresca tabla
  } catch (err) {
    console.error("❌ Error cancelando cliente:", err);
    mostrarToast("❌ Error de conexión al cancelar cliente", "error");
  }
}


let colaSeleccionada = null;
let clienteSeleccionado = null;
let datosFormularioDespacho = {};

async function abrirModalDespacho(idCola, idCliente, direccion) {
  colaSeleccionada = idCola;
  clienteSeleccionado = idCliente;

  // Capturar tarifa desde la fila de la cola
  const tarifaEl = document.getElementById("tarifaCliente_" + idCola);
  const tarifa = tarifaEl ? tarifaEl.value.trim() : "";

  // 👉 Validar que el operador haya colocado la tarifa
  if (!tarifa) {
    mostrarToast("⚠️ Debes colocar la tarifa antes de asignar el despacho", "error");
    return; // 🚫 no abrir modal
  }

  // Pasar valores al modal
  document.getElementById("modalClienteId").value = idCliente;
  document.getElementById("modalOrigen").value = direccion || "";
  document.getElementById("modalTarifa").value = tarifa;

  // Capturar valores del formulario principal
  datosFormularioDespacho = {
    tipoDespacho: document.getElementById("tipoDespacho").value,
    telefono: document.getElementById("desTelefono").value,
    nombre: document.getElementById("desNombre").value,
    origen: document.getElementById("desOrigen").value
  };

  // Validar disponibilidad de conductores
  try {
    const res = await apiFetch("/conductores/en_turno_disponibles");
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      mostrarToast("⚠️ No hay conductores disponibles en turno", "error");
      return;
    }
  } catch (err) {
    console.error("❌ Error validando disponibilidad de conductores:", err);
    mostrarToast("❌ No se pudo verificar disponibilidad de conductores", "error");
    return;
  }

  // Mostrar modal
  const modal = document.getElementById("modalCrearDespacho");
  modal.classList.remove("hidden");

  // Poblar selects
  await cargarConductoresModal();
  await cargarAutosModal();
}

async function cargarConductoresModal() {
  try {
    const res = await apiFetch("/conductores/en_turno_disponibles");
    const data = await res.json();
    const select = document.getElementById("selectConductor");
    select.innerHTML = "";

    if (Array.isArray(data) && data.length > 0) {
      data.forEach(t => {
        const c = t.conductor || t;
        const a = t.auto || {};
        if (c && c.id_conductor) {
          const option = document.createElement("option");
          option.value = c.id_conductor;
          option.textContent = `${c.codigo} - ${c.nombre} (${a.nro_placa || a.placa || "sin auto"})`;
          select.appendChild(option);
        }
      });
    } else {
      select.innerHTML = '<option disabled>No hay conductores disponibles</option>';
    }
  } catch (err) {
    console.error("❌ Error cargando conductores:", err);
    mostrarToast("❌ No se pudieron cargar conductores", "error");
  }
}

async function cargarAutosModal() {
  try {
    const res = await apiFetch("/conductores/en_turno_disponibles");
    const data = await res.json();
    const sel = document.getElementById("selectAuto");
    sel.innerHTML = "";

    if (Array.isArray(data) && data.length > 0) {
      data.forEach(t => {
        const a = t.auto || t;
        const c = t.conductor || {};
        if (a && a.id_auto) {
          const opt = document.createElement("option");
          opt.value = a.id_auto;
          opt.textContent = `${a.nro_placa || a.placa || "—"} - ${c.nombre || "sin conductor"}`;
          sel.appendChild(opt);
        }
      });
    } else {
      sel.innerHTML = '<option disabled>No hay autos disponibles</option>';
    }
  } catch (err) {
    console.error("❌ Error cargando autos disponibles:", err);
    mostrarToast("❌ No se pudieron cargar autos", "error");
  }
}

document.getElementById("btnConfirmarDespacho").onclick = async () => {
  const conductorId = document.getElementById("selectConductor").value;
  const autoId = document.getElementById("selectAuto").value;
  const origen = document.getElementById("modalOrigen").value.trim();
  const clienteId = document.getElementById("modalClienteId").value;
  const tarifa = document.getElementById("modalTarifa").value;

  if (!clienteId || !conductorId || !autoId || !origen || !tarifa) {
    mostrarToast("⚠️ Debes completar origen, cliente, conductor, auto y tarifa", "error");
    return;
  }

  const payload = {
    origen_despacho: origen,
    cliente_id: clienteId,
    conductor_id: conductorId,
    auto_id: autoId,
    tarifa,
    estado_despacho: "en curso",
    tipo_despacho: datosFormularioDespacho.tipoDespacho,
    telefono: datosFormularioDespacho.telefono,
    nombre: datosFormularioDespacho.nombre,
    cola_id: colaSeleccionada
  };

  try {
    const res = await apiFetch("/despachos/", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const result = await res.json();
      mostrarToast("✅ Despacho creado correctamente (ID " + result.id_despacho + ")", "success");
      document.getElementById("modalCrearDespacho").classList.add("hidden");
      colaSeleccionada = null;
      clienteSeleccionado = null;
      await cargarColaClientes();
    } else {
      const error = await res.json();
      mostrarToast("❌ Error al crear despacho: " + (error.error || res.status), "error");
    }
  } catch (err) {
    console.error("❌ Error creando despacho:", err);
    mostrarToast("❌ Error de conexión al crear despacho", "error");
  }
};

// Listener para botón Cancelar
document.addEventListener("click", (event) => {
  if (event.target.id === "btnCancelarDespacho") {
    const modal = document.getElementById("modalCrearDespacho");
    modal.classList.add("hidden");
    colaSeleccionada = null;
    clienteSeleccionado = null;
    datosFormularioDespacho = {};
    mostrarToast("❌ Despacho cancelado", "info"); // opcional
  }
});





