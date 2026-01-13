// ===============================
// modales_tipo_despacho.js
// Lógica exclusiva para modal de Reserva
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOMContentLoaded disparado (modales_tipo_despacho.js)");
  console.log("📍 Ejecutando lógica de reservas");

  const tipor = document.getElementById("tipoDespacho");
  const modalReserva1 = document.getElementById("modalDespachoReserva");

  if (modalReserva1) {
    modalReserva1.addEventListener("hidden.bs.modal", () => {
      console.log("🔄 Modal reserva cerrado, reiniciando select…");
      if (tipor) tipor.value = "";
      const form = modalReserva1.querySelector("form");
      if (form) form.reset();
    });
  } 
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key.toLowerCase() === "r") {
      event.preventDefault(); // evita el refresh del navegador

      const modalReservas = document.getElementById("modalListaReservas");
      if (modalReservas) {
        const modalInstance = new bootstrap.Modal(modalReservas);
        modalInstance.show();

        // Cargar reservas próximas a vencerse
        cargarReservasPorVencer();
      }
    }
  });
  
  // -------------------------------
  // 📌 Inicialización de modal Reserva
  // -------------------------------
  const modalReserva = document.getElementById("modalDespachoReserva");
  if (modalReserva) {
    window.modalReservaInstance = new bootstrap.Modal(modalReserva);
    console.log("✅ Instancia modalReserva creada");
  }
  // -------------------------------
// 📌 Select tipoDespacho → abrir modal Reserva
// -------------------------------
  const tipo = document.getElementById("tipoDespacho");
  if (tipo) {
    tipo.addEventListener("change", () => {
      const val = tipo.value;
      if (val === "reserva") {
        if (window.modalReservaInstance) window.modalReservaInstance.show();
      }
    });
  }

  // -------------------------------
  // 📌 Listener de teléfono en modalReserva
  // -------------------------------
  const telefonoInput = document.getElementById("resTelefono");
  if (telefonoInput) {
    telefonoInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const telefono = telefonoInput.value.trim();
        const regexTelefono = /^(0276[0-9]{7}|04[0-9]{9})$/;

        if (!regexTelefono.test(telefono)) {
          mostrarToast("⚠️ Número de teléfono inválido.", "error");
          return;
        }

        try {
          const resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
          const dataCliente = await resCliente.json();

          if (resCliente.ok && dataCliente.existe) {
            document.getElementById("resCliente").value = dataCliente.nombre || "";
            document.getElementById("resOrigen").value = dataCliente.direccion || "";
            document.getElementById("resCliente").setAttribute("readonly", true);
            document.getElementById("resOrigen").setAttribute("readonly", true);
            mostrarToast("✅ Cliente encontrado. Completa destino, fecha y hora.", "success");
          } else {
            document.getElementById("resCliente").removeAttribute("readonly");
            document.getElementById("resOrigen").removeAttribute("readonly");
            document.getElementById("resCliente").value = "";
            document.getElementById("resOrigen").value = "";
            mostrarToast("ℹ️ Cliente nuevo. Ingresa todos los datos.", "info");
          }
        } catch (err) {
          console.error("Error buscando cliente:", err);
          mostrarToast("❌ No se pudo conectar al servidor", "error");
        }
      }
    });
  }

  // -------------------------------
  // 📌 Función crearReserva
  // -------------------------------
  async function crearReserva() {
    const telefono = document.getElementById("resTelefono").value.trim();
    const clienteNombre = document.getElementById("resCliente").value.trim();
    const origen = document.getElementById("resOrigen").value.trim();
    const destino = document.getElementById("resDestino").value.trim();
    const fecha = document.getElementById("resFecha").value;
    const hora = document.getElementById("resHora").value;

    if (!telefono || !clienteNombre || !origen || !destino || !fecha || !hora) {
      mostrarToast("⚠️ Debes completar todos los campos de la reserva", "error");
      return;
    }

    const regexTelefono = /^(0276[0-9]{7}|04[0-9]{9})$/;
    if (!regexTelefono.test(telefono)) {
      mostrarToast("⚠️ Número de teléfono inválido.", "error");
      return;
    }

    let clienteId;
    try {
      const resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
      const dataCliente = await resCliente.json();

      if (resCliente.ok && dataCliente.existe) {
        clienteId = dataCliente.id_cliente;
      } else {
        const nuevoClienteRes = await apiFetch("/clientes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ telefono, nombre: clienteNombre, direccion: origen })
        });
        const nuevoClienteData = await nuevoClienteRes.json();
        if (nuevoClienteRes.ok) {
          clienteId = nuevoClienteData.id_cliente;
        } else {
          mostrarToast(nuevoClienteData.error || "❌ Error al registrar cliente", "error");
          return;
        }
      }

      const resReserva = await apiFetch("/reservas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cliente_id: clienteId, origen, destino, fecha, hora, estado: "activo" })
      });
      const dataReserva = await resReserva.json();

      if (resReserva.ok) {
        mostrarToast(`✅ Reserva creada con ID: ${dataReserva.reserva.id_reserva}`, "success");
        bootstrap.Modal.getInstance(modalReserva).hide();
        programarAlerta(dataReserva.reserva);
                
      } else {
        mostrarToast(dataReserva.error || "❌ Error al crear la reserva", "error");
      }
    } catch (err) {
      console.error("Error creando reserva:", err);
      mostrarToast("❌ No se pudo conectar al servidor", "error");
    }
  }

  // -------------------------------
  // 📌 Programar alerta de reserva
  // -------------------------------
  function programarAlerta(reserva) {
    const fechaHoraReserva = new Date(`${reserva.fecha}T${reserva.hora}`);
    const ahora = new Date();
    const msHastaReserva = fechaHoraReserva - ahora;
    const msHastaAlerta = msHastaReserva - (15 * 60 * 1000);

    if (msHastaReserva <= 0) return;
    if (msHastaAlerta > 0) {
      setTimeout(() => {
        mostrarToast(`⏰ Alerta: Reserva #${reserva.id_reserva} en 15 minutos`, "info");
      }, msHastaAlerta);
    } else {
      mostrarToast(`⏰ Alerta: Reserva #${reserva.id_reserva} en menos de 15 minutos`, "warning");
    }
  }

  // -------------------------------
  // 📌 Enganchar botones
  // -------------------------------
  const btnCrearReserva = document.getElementById("btnCrearReserva");
  if (btnCrearReserva) btnCrearReserva.addEventListener("click", crearReserva);
  
  ////Función cargar reservas en modal (por implementar)/////
 async function cargarReservasPorVencer() {
    try {
      const res = await apiFetch("/reservas/por_vencer"); // 👈 usar el endpoint correcto
      const data = await res.json();
      console.log("📡 Datos recibidos en reservas:", JSON.stringify(data, null, 2));

      const tbody = document.querySelector("#tablaReservas tbody");
      tbody.innerHTML = "";

      // 👇 filtrar solo las activas
      const activas = Array.isArray(data.reservas) 
        ? data.reservas.filter(r => r.estado === "activo") 
        : [];

      if (activas.length > 0) {
        activas.forEach(r => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${r.id_reserva}</td>
            <td>${r.cliente?.nombre || "—"}</td>
            <td>${r.origen}</td>
            <td>${r.destino}</td>
            <td>${r.fecha}</td>
            <td>${r.hora}</td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="6" class="text-center">No hay reservas próximas a vencerse</td>`;
        tbody.appendChild(tr);
      }
    } catch (err) {
      console.error("❌ Error cargando reservas:", err);
      mostrarToast("❌ No se pudo cargar la lista de reservas", "error");
    }
  }


});
