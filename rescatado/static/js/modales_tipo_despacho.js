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

    let clienteId;

    try {
      // Buscar cliente por teléfono
      let resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
      let dataCliente = await resCliente.json();

      if (resCliente.ok && dataCliente.existe !== false) {
        clienteId = dataCliente.id_cliente;
      } else {
        // Registrar cliente si no existe
        const nuevoClienteRes = await apiFetch("/clientes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ telefono, nombre: clienteNombre, direccion: origen })
        });
        const nuevoClienteData = await nuevoClienteRes.json();
        clienteId = nuevoClienteData.id_cliente;
      }

      // Crear la reserva
      const resReserva = await apiFetch("/reservas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cliente_id: clienteId, origen, destino, fecha, hora, estado: "activo" })
      });
      const dataReserva = await resReserva.json();

      if (resReserva.ok) {
        mostrarToast(`✅ Reserva creada con ID: ${dataReserva.reserva.id_reserva}`, "success");
        bootstrap.Modal.getInstance(document.getElementById("modalDespachoReserva")).hide();
      } else {
        mostrarToast("❌ Error al crear la reserva", "error");
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
