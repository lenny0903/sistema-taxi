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
      <td>${c.iteraciones}</td>
     <!-- <td>-->
        <!--<button class="btn btn-success" -->
               <!--onclick="pasarADespachoMultiple(${c.id_lista_multiple}, ${c.iteraciones}, '${c.telefono}', '${c.nombre}', '${c.direccion}')"-->
               <!-- <button class="btn btn-success" -->
          <!--Despachar-->
        <!--</button>-->
      <!--</td>-->

    `;
    tbody.appendChild(tr);
  });
}


// 4. Pasar cliente de lista de espera → despacho múltiple
// Pasar cliente de lista de espera → despacho múltiple
async function pasarADespachoMultiple(idCola, iteracionesGuardadas, telefono) {
  try {
    const disponibles = await cargarConductoresEnTurnoDespacho();
    if (!disponibles || disponibles.length === 0) {
      mostrarToast("❌ No hay conductores disponibles en turno", "error");
      return;
    }

    if (disponibles.length < iteracionesGuardadas) {
      mostrarToast(
        `❌ Solo hay ${disponibles.length} conductores disponibles, se requieren ${iteracionesGuardadas}`,
        "error"
      );
      return;
    }

    const res = await fetch(`/lista_espera_multiple/api/despacho_multiple/${idCola}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ iteraciones: iteracionesGuardadas })
    });
    const data = await res.json();

    if (data.status === "ok") {
      bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modalTablaListaEsperaMultiple")
      ).hide();

      // 👉 Solo pasar el teléfono y disparar la lógica de consulta
      const telEl = document.getElementById("modalTelefono");
      if (telEl) {
        telEl.value = telefono;
        telEl.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" }));
      }

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

// Función para verificar disponibilidad y disparar alarma
async function verificarDisponibilidadListaMultiple() {
  try {
    // 1. Obtener lista de espera múltiple
    const resLista = await fetch("/lista_espera_multiple/api/cola_multiple");
    const clientes = await resLista.json();

    // 2. Obtener conductores disponibles
    const disponibles = await cargarConductoresEnTurnoDespacho();

    // 3. Revisar cada cliente en espera
    clientes.forEach(c => {
      if (c.estado === "EN_ESPERA_MULTIPLE") {
        if (disponibles.length >= c.iteraciones) {
          // 👉 Alarma para el operador
          mostrarToast(
            `⏰ Alerta: Cliente ${c.nombre} (${c.telefono}) tiene disponibilidad de ${disponibles.length} conductores para ${c.iteraciones} iteraciones`,
            "info"
          );

          // Opcional: sonido de alerta
          const audio = new Audio("/static/sounds/alerta.mp3");
          audio.play();
        }
      }
    });
  } catch (err) {
    //console.error("Error verificando disponibilidad:", err);
    //mostrarToast("❌ Error verificando disponibilidad de conductores", "error");
  }
}

// 4. Programar verificación cada X segundos (ej: cada 30s)
setInterval(verificarDisponibilidadListaMultiple, 30000);
