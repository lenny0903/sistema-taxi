document.addEventListener("DOMContentLoaded", () => {
  const formDespacho = document.getElementById("formDespacho");
  const telefonoInput = document.getElementById("desTelefono");
  const btnEnviar = document.getElementById("btnEnviarDespacho");
  const modalCola = document.getElementById("modalColaClientes");
  const tbodyCola = document.getElementById("tablaColaClientes");
  const btnCerrarCola = document.getElementById("btnCerrarCola");

  // Estado inicial
  btnEnviar.disabled = true;

  // Submit → crear cola
  formDespacho.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (btnEnviar.disabled) {
      alert("⚠️ Primero valida o crea el cliente antes de enviar.");
      return;
    }
    await crearCola();
  });

  // Enter en teléfono → validar cliente
  telefonoInput.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      validarClientePorTelefono();
    }
  });

  // Alt+C → abrir modal cola
  document.addEventListener("keydown", (event) => {
    if (event.altKey && event.key.toLowerCase() === "c") {
      event.preventDefault();
      abrirModalCola();
    }
  });

  // Botón cerrar modal cola
  if (btnCerrarCola) {
    btnCerrarCola.addEventListener("click", cerrarModalCola);
  }
});

// ==================== Funciones auxiliares ====================

function activarCamposDespacho(habilitar) {
  const btnEnviar = document.getElementById("btnEnviarDespacho");
  if (btnEnviar) btnEnviar.disabled = !habilitar;
}

async function validarClientePorTelefono() {
  const telefono = document.getElementById('desTelefono').value.trim();
  if (!telefono) return null;

  try {
    const res = await apiFetch(`/clientes/buscar?telefono=${telefono}`);
    const data = await res.json();
    console.log("Respuesta backend:", data); // 👀 para ver estructura real

    let cliente = null;
    if (Array.isArray(data) && data.length > 0) {
      cliente = data[0];
    } else if (data && typeof data === "object" && data.cliente) {
      cliente = data.cliente;
    }

    if (cliente) {
      document.getElementById('desNombre').value = cliente.nombre || '';
      document.getElementById('desOrigen').value = cliente.direccion || '';
      activarCamposDespacho(true);
      return cliente;
    } else {
      document.getElementById('desNombre').value = '';
      document.getElementById('desOrigen').value = '';
      activarCamposDespacho(false);
      abrirModalCrearCliente(telefono);
      return null;
    }
  } catch (err) {
    console.error("❌ Error validando cliente:", err);
    return null;
  }
}


async function crearCola() {
  const telefono = document.getElementById("desTelefono").value.trim();
  const nombre   = document.getElementById("desNombre").value.trim();
  const origen   = document.getElementById("desOrigen").value.trim();
  const tipo     = document.getElementById("tipoDespacho").value;

  let nro_autos = 1;
  if (tipo && !isNaN(tipo)) nro_autos = parseInt(tipo);

  const payload = { telefono, nombre, origen, nro_autos };

  try {
    const res = await apiFetch("/cola_despachos", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      mostrarToast("❌ Error al crear cola: " + res.status, "error");
      return;
    }
    await res.json();
    mostrarToast("✅ Cliente agregado a la cola", "success");
    document.getElementById("formDespacho").reset();
    activarCamposDespacho(false);
  } catch (err) {
    console.error("❌ Error enviando despacho:", err);
  }
}

function abrirModalCrearCliente(telefono) {
  const modal = document.getElementById("modalCrearCliente");
  modal.classList.remove("hidden");
  document.getElementById("btnGuardarCliente").onclick = async () => {
    const nombre = document.getElementById("nuevoClienteNombre").value.trim();
    const direccion = document.getElementById("nuevoClienteDireccion").value.trim();
    if (!validarNombre(nombre)) {
      alert("❌ Nombre inválido.");
      return;
    }
    const nuevoCliente = { telefono, nombre, direccion };
    const resPost = await apiFetch("/clientes/", {
      method: "POST",
      body: JSON.stringify(nuevoCliente)
    });
    const result = await resPost.json();
    if (resPost.ok) {
      mostrarToast("✅ Cliente creado correctamente", "info");
      document.getElementById('desNombre').value = nombre;
      document.getElementById('desOrigen').value = direccion;
      activarCamposDespacho(true);
    } else {
      mostrarToast("❌ Error al crear cliente: " + (result.error || "verifica datos"), "error");
    }
    cerrarModalCrearCliente();
  };
  document.getElementById("btnCancelarModal").onclick = cerrarModalCrearCliente;
}

function cerrarModalCrearCliente() {
  const modal = document.getElementById("modalCrearCliente");
  modal.classList.add("hidden");
}

function validarNombre(nombre) {
  return nombre && nombre.trim().length >= 2;
}

// Cola de clientes
function abrirModalCola() {
  const modalCola = document.getElementById("modalColaClientes");
  modalCola.classList.remove("hidden");
  cargarColaClientes();
}

function cerrarModalCola() {
  const modalCola = document.getElementById("modalColaClientes");
  modalCola.classList.add("hidden");
}

async function cargarColaClientes() {
  const tbodyCola = document.getElementById("tablaColaClientes");
  try {
    const res = await apiFetch("/cola_despachos/");
    const data = await res.json();
    tbodyCola.innerHTML = "";
    if (!Array.isArray(data) || data.length === 0) {
      tbodyCola.innerHTML = `<tr><td colspan="6" class="text-center">No hay clientes en cola</td></tr>`;
      return;
    }
    data.forEach(cliente => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="border px-2 py-1">${cliente.cliente?.telefono || ""}</td>
        <td class="border px-2 py-1">${cliente.cliente?.nombre || ""}</td>
        <td class="border px-2 py-1">${cliente.cliente?.direccion || ""}</td>
        <td class="border px-2 py-1">${cliente.nro_autos}</td>
        <td class="border px-2 py-1">
          <input type="number" id="tarifaCliente_${cliente.cliente?.id_cliente}" 
                class="border p-1 w-24 rounded" 
                placeholder="Bs." min="0">
        </td>
        <td class="border px-2 py-1">${cliente.estado}</td>
        <td class="border px-2 py-1">
         <button 
            onclick="abrirModalDespacho(${cliente.id_cola}, ${cliente.cliente?.id_cliente}, '${cliente.cliente?.direccion || ""}')" 
            class="bg-blue-600 text-white px-2 py-1 rounded">
            Asignar
          </button>

          <button onclick="cancelarCliente(${cliente.id_cola})" class="bg-red-600 text-white px-2 py-1 rounded">Cancelar</button>
        </td>
      `;
      tbodyCola.appendChild(tr);
    });
  } catch (err) {
    console.error("❌ Error cargando cola:", err);
  }
}
/////Para modal de asignación de conductor y vehículo/////
let colaSeleccionada = null; // id de la cola que estamos asignando
let clienteSeleccionado = null;
let datosFormularioDespacho = {};

async function abrirModalDespacho(idCola, idCliente, direccion) {
  colaSeleccionada = idCola;
  clienteSeleccionado = idCliente;

  // Capturar valores del formulario principal
  datosFormularioDespacho = {
    tipoDespacho: document.getElementById("tipoDespacho").value,
    telefono: document.getElementById("desTelefono").value,
    nombre: document.getElementById("desNombre").value,
    origen: document.getElementById("desOrigen").value
  };

  // 🔎 Validar disponibilidad antes de abrir modal
  try {
    const res = await apiFetch("/conductores/en_turno_disponibles");
    const data = await res.json();

    if (!Array.isArray(data) || data.length === 0) {
      mostrarToast("⚠️ No hay conductores disponibles en turno", "error");
      return; // 🚫 no abrir modal
    }
  } catch (err) {
    console.error("❌ Error validando disponibilidad de conductores:", err);
    mostrarToast("❌ No se pudo verificar disponibilidad de conductores", "error");
    return;
  }

  // Capturar tarifa desde la fila de la cola
  const tarifaEl = document.getElementById("tarifaCliente_" + idCliente);
  const tarifa = tarifaEl ? tarifaEl.value : "";

  // Pasar valores al modal oculto
  document.getElementById("modalClienteId").value = idCliente;
  document.getElementById("modalOrigen").value = direccion || "";
  document.getElementById("modalTarifa").value = tarifa;

  // Mostrar modal solo si hay disponibilidad
  const modal = document.getElementById("modalCrearDespacho");
  modal.classList.remove("hidden");

  // Cargar opciones dinámicas
  await cargarConductoresModal();
  await cargarAutosModal();
}


// Poblar select de conductores en turno dentro del modal
async function cargarConductoresModal() {
  try {
    const res = await apiFetch("/conductores/en_turno_disponibles");
    const data = await res.json();
    console.log("Conductores en turno disponibles:", data);

    const select = document.getElementById("selectConductor");
    select.innerHTML = "";

    if (Array.isArray(data) && data.length > 0) {
      data.forEach(t => {
        const c = t.conductor || t; // puede venir como {conductor:{...}} o directo
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

// Poblar select de autos disponibles dentro del modal
async function cargarAutosModal() {
  try {
    const res = await apiFetch("/conductores/en_turno_disponibles");
    const data = await res.json();
    console.log("Autos en turno recibidos:", data);

    const sel = document.getElementById("selectAuto");
    sel.innerHTML = "";

    if (Array.isArray(data) && data.length > 0) {
      data.forEach(t => {
        const a = t.auto || t; // puede venir como {auto:{...}} o directo
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



document.getElementById("btnConfirmarDespacho").onclick = async () => {
  const conductorId = document.getElementById("selectConductor")?.value;
  const autoId = document.getElementById("selectAuto")?.value;
  const origen = document.getElementById("modalOrigen")?.value?.trim();
  const clienteId = document.getElementById("modalClienteId")?.value;
  const tarifa = document.getElementById("modalTarifa")?.value || null;
  
  // Logs de depuración
  console.log("clienteId:", clienteId);
  console.log("conductorId:", conductorId);
  console.log("autoId:", autoId);
  console.log("origen:", origen);
  console.log("tarifa:", tarifa);
  if (!clienteId || !conductorId || !autoId || !origen || !tarifa) {
    mostrarToast("⚠️ Debes completar origen, cliente, conductor, auto y tarifa", "error");
    return;
  }

  const payload = {
    origen_despacho: origen,
    cliente_id: clienteId,
    conductor_id: conductorId,
    auto_id: autoId,
    tarifa: tarifa,
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
///Cancelar cliente de la cola///
async function cancelarCliente(idCola) {
  try {
    const res = await apiFetch(`/cola_despachos/${idCola}`, { method: "DELETE" });
    if (res.ok) {
      mostrarToast("✅ Cliente cancelado de la cola", "success");
      await cargarColaClientes(); // refrescar tabla
    } else {
      const error = await res.json();
      mostrarToast("❌ Error al cancelar cliente: " + (error.error || res.status), "error");
    }
  } catch (err) {
    console.error("❌ Error cancelando cliente:", err);
    mostrarToast("❌ Error de conexión al cancelar cliente", "error");
  }
}
