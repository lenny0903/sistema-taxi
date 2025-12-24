// ===============================
// modales.js
// Lógica para modales de Reserva y Despacho Múltiple
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOMContentLoaded disparado (modales.js)");

  // -------------------------------
  // 📌 Inicialización de modales
  // -------------------------------
  const modalMultiple = document.getElementById("modalDespachoMultiple");
  const modalReserva = document.getElementById("modalDespachoReserva");

  if (modalMultiple) {
    window.modalMultipleInstance = new bootstrap.Modal(modalMultiple);
    console.log("✅ Instancia modalMultiple creada");
  }

  if (modalReserva) {
    window.modalReservaInstance = new bootstrap.Modal(modalReserva);
    console.log("✅ Instancia modalReserva creada");
  }

  // -------------------------------
  // 📌 Select tipoDespacho
  // -------------------------------
  const tipo = document.getElementById("tipoDespacho");
  if (tipo) {
    tipo.addEventListener("change", async () => {
      const val = tipo.value;

      if (val === "reserva") {
        if (window.modalReservaInstance) window.modalReservaInstance.show();
        return;
      }

      if (["2","3","4"].includes(val)) {
        const conductores = await cargarConductoresEnTurnoDespacho();
        if (!Array.isArray(conductores) || conductores.length < parseInt(val, 10)) {
          mostrarToast(`🚦 No hay suficientes conductores → se requieren ${val}, disponibles: ${conductores.length}`, "error");
          return;
        }
        window.nroVehiculos = parseInt(val, 10);
        if (window.modalMultipleInstance) window.modalMultipleInstance.show();
      }
    });
  }

  // -------------------------------
  // 📌 Validación de disponibilidad
  // -------------------------------
  function validarDisponibilidad() { 
    const nroVehiculosEl = document.getElementById("nroVehiculos");
    const msgDisponibilidad = document.getElementById("msgDisponibilidad");
    const formDatosComunes = document.getElementById("formDatosComunes");
    const btnCrear = document.getElementById("btnCrearDespachoMultiple");

    const nroVehiculos = parseInt(nroVehiculosEl?.value || 0, 10);
    console.log("🚦 Validando disponibilidad con:", nroVehiculos);

    if (!nroVehiculos || nroVehiculos <= 0) {
      if (msgDisponibilidad) msgDisponibilidad.textContent = "⚠️ Ingrese un número válido de vehículos.";
      console.warn("⚠️ Número inválido:", nroVehiculos);
      return;
    }

    // Habilitar datos comunes y botón crear
    if (msgDisponibilidad) msgDisponibilidad.textContent = "✅ Disponibilidad confirmada para " + nroVehiculos + " vehículos.";
    if (formDatosComunes) formDatosComunes.classList.remove("d-none");
    if (btnCrear) btnCrear.removeAttribute("disabled");

    // Guardar en estado global para usar al crear
    window.nroVehiculos = nroVehiculos;
    console.log("✅ Datos comunes habilitados y nroVehiculos =", window.nroVehiculos);
  }
  // Validar teléfono al presionar Enter en el input
    const telefonoInput = document.getElementById("resTelefono");
    if (telefonoInput) {
      telefonoInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          const telefono = telefonoInput.value.trim();
          const regexTelefono = /^(0276|0412|0414|0416|0424|0426)[0-9]{7}$/;

          if (!regexTelefono.test(telefono)) {
            mostrarToast("⚠️ Número de teléfono inválido. Debe tener 11 dígitos y prefijo válido.", "error");
            return;
          }

          try {
            const resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
            const dataCliente = await resCliente.json();

            if (resCliente.ok && dataCliente.existe !== false) {
              // Cliente encontrado → rellenar nombre y origen
              document.getElementById("resCliente").value = dataCliente.nombre || "";
              document.getElementById("resOrigen").value = dataCliente.direccion || "";

              // Bloquear edición de nombre y origen
              document.getElementById("resCliente").setAttribute("readonly", true);
              document.getElementById("resOrigen").setAttribute("readonly", true);

              mostrarToast("✅ Cliente encontrado. Completa destino, fecha y hora.", "success");
            } else {
              // Cliente nuevo → habilitar todos los campos
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

    // Programar alerta 15 minutos antes de la reserva
   function programarAlerta(reserva) {
      const fechaHoraReserva = new Date(`${reserva.fecha}T${reserva.hora}`);
      const ahora = new Date();
      const msHastaReserva = fechaHoraReserva - ahora;
      const msHastaAlerta = msHastaReserva - (15 * 60 * 1000);

      if (msHastaReserva <= 0) {
        // Caso: la reserva ya pasó → no mostrar nada
        return;
      }

      if (msHastaAlerta > 0) {
        // Caso normal: falta más de 15 min → programar alerta
        setTimeout(() => {
          mostrarToast(`⏰ Alerta: Reserva #${reserva.id_reserva} en 15 minutos`, "info");
        }, msHastaAlerta);
      } else {
        // Caso especial: ya estamos dentro de los 15 min → alerta inmediata
        mostrarToast(`⏰ Alerta: Reserva #${reserva.id_reserva} en menos de 15 minutos`, "warning");
      }
    }

    // Convertir hora "HH:MM" a formato 12h con AM/PM
  function formatoHora12(hora24) {
    if (!hora24) return "";
    const [h, m] = hora24.split(":").map(Number);
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 || 12; // convierte 0 → 12
    return `${h12}:${m.toString().padStart(2, "0")} ${ampm}`;
  }

  // -------------------------------
  // 📌 Atajo de teclado Ctrl+R → abrir listado de reservas
  // -------------------------------
  document.addEventListener("keydown", async (event) => {
    if (event.ctrlKey && event.key.toLowerCase() === "r") {
      event.preventDefault(); // evita recarga del navegador

      try {
        const res = await apiFetch("/reservas");
        const data = await res.json();

        const tbody = document.querySelector("#tablaReservas tbody");
        tbody.innerHTML = ""; // limpiar tabla

        // 🔒 Función para filtrar solo reservas futuras
        function esReservaFutura(reserva) {
          const fechaHoraReserva = new Date(`${reserva.fecha}T${reserva.hora}`);
          const ahora = new Date();
          return fechaHoraReserva >= ahora;
        }

        // Mostrar solo reservas futuras
        data.reservas
          .filter(esReservaFutura)
          .forEach(r => {
            const fila = `
              <tr>
                <td>${r.id_reserva}</td>
                <td>${r.cliente?.nombre || ""}</td>
                <td>${r.origen}</td>
                <td>${r.destino}</td>
                <td>${r.fecha}</td>
                <td>${formatoHora12(r.hora)}</td>
              </tr>`;
            tbody.insertAdjacentHTML("beforeend", fila);
          });

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById("modalListaReservas"));
        modal.show();
      } catch (err) {
        console.error("Error cargando reservas:", err);
        mostrarToast("❌ No se pudo cargar el listado de reservas", "error");
      }
    }
  });


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

    // Validación de campos obligatorios
    if (!telefono || !clienteNombre || !origen || !destino || !fecha || !hora) {
      mostrarToast("⚠️ Debes completar todos los campos de la reserva", "error");
      return;
    }

    // Validación de teléfono (11 dígitos con prefijo válido)
    const regexTelefono = /^(0276|0412|0414|0416|0424|0426)[0-9]{7}$/;
    if (!regexTelefono.test(telefono)) {
      mostrarToast("⚠️ Número de teléfono inválido. Debe tener 11 dígitos y prefijo válido.", "error");
      return;
    }

    let clienteId;

    try {
      // Paso 1: buscar cliente por teléfono
      const resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
      const dataCliente = await resCliente.json();

      if (resCliente.ok && dataCliente.existe !== false) {
        clienteId = dataCliente.id_cliente;
      } else {
        // Paso 2: registrar cliente si no existe
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

      // Paso 3: crear la reserva
      const resReserva = await apiFetch("/reservas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cliente_id: clienteId, origen, destino, fecha, hora, estado: "activo" })
      });
      const dataReserva = await resReserva.json();

      if (resReserva.ok) {
        mostrarToast(`✅ Reserva creada con ID: ${dataReserva.reserva.id_reserva}`, "success");
        bootstrap.Modal.getInstance(document.getElementById("modalDespachoReserva")).hide();
        programarAlerta(dataReserva.reserva);
      } else {
        mostrarToast(dataReserva.error || "❌ Error al crear la reserva", "error");
      }
    } catch (err) {
      console.error("Error:", err);
      mostrarToast("❌ No se pudo conectar al servidor", "error");
    }
  }



  // -------------------------------
  // 📌 Función crearDespachoMultiple
  // -------------------------------
  async function crearDespachoMultiple() { 
    const origen = document.getElementById("multiOrigen")?.value.trim();
    const destino = document.getElementById("multiDestino")?.value.trim();
    const fecha = document.getElementById("multiFecha")?.value;
    const hora = document.getElementById("multiHora")?.value;
    const nroVehiculos = parseInt(window.nroVehiculos || 0, 10);

    if (!origen || !destino || !fecha || !hora || nroVehiculos <= 0) {
      mostrarToast("⚠️ Debes completar todos los campos y validar disponibilidad", "error");
      return;
    }

    try {
      const conductores = await cargarConductoresEnTurnoDespacho();
      if (!Array.isArray(conductores) || conductores.length < nroVehiculos) {
        mostrarToast(`❌ No hay suficientes conductores. Requeridos: ${nroVehiculos}, disponibles: ${conductores.length}`, "error");
        return;
      }

      const seleccion = conductores.slice(0, nroVehiculos).map(c => c.id_conductor);

      const resDespacho = await apiFetch("/despachos/multiple", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origen, destino, fecha, hora, nro_vehiculos: nroVehiculos, conductores: seleccion })
      });
      const data = await resDespacho.json();

      if (resDespacho.ok) {
        mostrarToast(`✅ Despacho múltiple creado con ID: ${data.id_despacho}`, "success");
        bootstrap.Modal.getInstance(document.getElementById("modalDespachoMultiple")).hide();
        window.nroVehiculos = 0;
      } else {
        mostrarToast("❌ Error al realizar el despacho múltiple", "error");
      }
    } catch (err) {
      console.error("Error creando despacho múltiple:", err);
      mostrarToast("❌ No se pudo conectar al servidor", "error");
    }
  }

  // -------------------------------
  // 📌 Enganchar botones
  // -------------------------------
  const btnCrearReserva = document.getElementById("btnCrearReserva");
  const btnCrearDespachoMultiple = document.getElementById("btnCrearDespachoMultiple");
  const btnValidarDisponibilidad = document.getElementById("btnValidarDisponibilidad");

  if (btnCrearReserva) btnCrearReserva.addEventListener("click", crearReserva);
  if (btnCrearDespachoMultiple) btnCrearDespachoMultiple.addEventListener("click", crearDespachoMultiple);
  if (btnValidarDisponibilidad) btnValidarDisponibilidad.addEventListener("click", validarDisponibilidad);
});
