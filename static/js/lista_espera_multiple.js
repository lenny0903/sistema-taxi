// 1. Autocompletar datos al ingresar teléfono
document.getElementById("telefono").addEventListener("keydown", async (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    const telefono = e.target.value;

    try {
      const res = await fetch(`/clientes/telefono/${telefono}`);
      const data = await res.json();

      if (data.existe) {
        document.getElementById("nombre").value = data.nombre;
        document.getElementById("direccion").value = data.direccion || "";
        // Guardamos id_cliente en dataset para usarlo al crear la cola
        document.getElementById("formColaMultiple").dataset.idCliente = data.id_cliente;
        mostrarToast("✅ Cliente encontrado", "success");
      } else {
        mostrarToast("❌ Cliente no encontrado", "error");
      }
    } catch (err) {
      console.error("Error buscando cliente:", err);
      mostrarToast("❌ Error de conexión con backend", "error");
    }
  }
});

// 2. Guardar cola múltiple
document.getElementById("formColaMultiple").addEventListener("submit", async (e) => {
  e.preventDefault();

  const idCliente = e.target.dataset.idCliente;
  const telefono = document.getElementById("telefono").value;
  const nombre = document.getElementById("nombre").value;
  const direccion = document.getElementById("direccion").value;
  const iteraciones = parseInt(document.getElementById("tipoDespacho").value, 10);

  try {
    // Opcional: actualizar cliente si cambió nombre/dirección
    await fetch(`/clientes/telefono/${telefono}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, direccion })
    });

    // Crear cola múltiple
    const payload = { 
      id_cliente: idCliente, 
      telefono, 
      nombre, 
      direccion, 
      iteraciones, 
      estado: "EN_ESPERA_MULTIPLE" 
    };

    const res = await fetch("/lista_espera_multiple/api/cola_multiple", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.status === "ok") {
      mostrarToast("✅ Cliente agregado a lista de espera múltiple", "success");
      bootstrap.Modal.getOrCreateInstance(document.getElementById("modalColaMultiple")).hide();
      await cargarListaEsperamultiple();
    } else {
      mostrarToast("❌ Error al crear cola múltiple", "error");
    }
  } catch (err) {
    console.error("Error creando cola múltiple:", err);
    mostrarToast("❌ Error de conexión con backend", "error");
  }
});

// 3. Renderizar tabla de lista de espera
async function cargarListaEsperamultiple() {
  const res = await fetch("/lista_espera_multiple/api/cola_multiple");
  const clientes = await res.json();
  renderListaEspera(clientes);
}

function renderListaEspera(clientes) {
  const tbody = document.querySelector("#tablaListaEspera tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  clientes.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${c.telefono}</td>
      <td>${c.nombre}</td>
      <td>${c.direccion}</td>
      <td>
        <button class="btn btn-success" onclick="pasarADespachoMultiple(${c.id_lista_multiple}, ${c.iteraciones}, '${c.telefono}', '${c.nombre}', '${c.direccion}')">
          Despachar
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}


// 4. Pasar cliente de lista de espera → despacho múltiple
// Pasar cliente de lista de espera → despacho múltiple
async function pasarADespachoMultiple(idCola, iteracionesGuardadas, telefono, nombre, direccion) {
  try {
    // 1. Validar disponibilidad de conductores
    const disponibles = await cargarConductoresEnTurnoDespacho();

    if (!disponibles || disponibles.length === 0) {
      mostrarToast("❌ No hay conductores disponibles en turno", "error");
      return;
    }

    // 2. Iteraciones guardadas en la tabla lista_espera_multiple
    const iteraciones = iteracionesGuardadas;

    // 3. Validar que disponibilidad >= iteraciones
    if (disponibles.length < iteraciones) {
      mostrarToast(
        `❌ Solo hay ${disponibles.length} conductores disponibles, se requieren ${iteraciones}`,
        "error"
      );
      return;
    }

    // 4. Llamar al backend para mover cliente a despacho múltiple
    const res = await fetch(`/lista_espera_multiple/api/despacho_multiple/${idCola}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ iteraciones })
    });
    const data = await res.json();

    if (data.status === "ok") {
      // Cerrar modal de lista de espera
      bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalTablaListaEsperaMultiple")
      ).hide();

      // 👉 Inyectar datos del cliente en los inputs del modal de despachos múltiples
      const telEl = document.getElementById("modalTelefono");
      if (telEl) telEl.value = telefono;

      const nombreEl = document.getElementById("modalCliente");
      if (nombreEl) nombreEl.value = nombre;

      const origenEl = document.getElementById("modalOrigen");
      if (origenEl) origenEl.value = direccion;

      // Abrir modal de despacho múltiple
      bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalDespachoMultiple")
      ).show();

      mostrarToast("✅ Cliente movido a despacho múltiple", "success");
    } else {
      mostrarToast("❌ Error al mover cliente a despacho múltiple", "error");
    }
  } catch (err) {
    console.error("Error en transición:", err);
    mostrarToast("❌ Error de conexión con backend", "error");
  }
}



// 5. Atajo de teclado Alt+E → abrir modal de lista de espera múltiple
document.addEventListener("keydown", async (e) => {
  if (e.altKey && e.key.toLowerCase() === "e") {
    e.preventDefault();
    try {
      await cargarListaEsperamultiple();
      const modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalTablaListaEsperaMultiple")
      );
      modal.show();
    } catch (err) {
      console.error("Error cargando lista de espera múltiple:", err);
      mostrarToast("❌ Error de conexión con backend", "error");
    }
  }
});

