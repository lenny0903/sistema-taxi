// ===============================
// dashboard.js (Parte 1)
// Archivo central de lógica del dashboard
// ===============================

// ✅ Único bloque DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOMContentLoaded disparado");
  //////SECCIÓN: Despachos Múltiples y Reserva//////
    // 🔹 Inicialización de modales
    const modalMultiple = document.getElementById("modalDespachoMultiple");
    const modalReserva = document.getElementById("modalDespachoReserva");

    if (modalMultiple) {
      window.modalMultipleInstance = new bootstrap.Modal(modalMultiple);
      console.log("✅ Instancia modalMultiple creada");
    } else {
      console.warn("⚠️ No se encontró #modalDespachoMultiple en el DOM");
    }

    if (modalReserva) {
      window.modalReservaInstance = new bootstrap.Modal(modalReserva);
      console.log("✅ Instancia modalReserva creada");
    } else {
      console.warn("⚠️ No se encontró #modalDespachoReserva en el DOM");
    }

    // 🔹 Listener del select tipoDespacho
    const tipo = document.getElementById("tipoDespacho");
    tipo.addEventListener("change", async () => {
      const val = tipo.value;

      // 🔹 Flujo de Reserva → siempre se abre, sin validar conductores
      if (val === "reserva") {
        if (window.modalReservaInstance) window.modalReservaInstance.show();
        return;
      }

      // 🔹 Flujo de Múltiple → validar conductores
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

    // 🔹 Validación de disponibilidad en modal múltiple
    const btnValidar = document.getElementById("btnValidarDisponibilidad");
    const msgDisponibilidad = document.getElementById("msgDisponibilidad");
    const formDatosComunes = document.getElementById("formDatosComunes");
    const btnCrear = document.getElementById("btnCrearDespachoMultiple");

    if (btnValidar) {
      btnValidar.addEventListener("click", () => {
        const nroVehiculos = document.getElementById("nroVehiculos").value;
        console.log("🚦 Validando disponibilidad con:", nroVehiculos);

        if (nroVehiculos && parseInt(nroVehiculos) > 0) {
          msgDisponibilidad.textContent = "✅ Disponibilidad confirmada para " + nroVehiculos + " vehículos.";
          formDatosComunes.classList.remove("d-none");
          btnCrear.removeAttribute("disabled");
          console.log("✅ Datos comunes habilitados");
        } else {
          msgDisponibilidad.textContent = "⚠️ Ingrese un número válido de vehículos.";
          console.warn("⚠️ Número inválido:", nroVehiculos);
        }
      });
    }
  // ✅ Declaración única
    const btnCrearReserva = document.getElementById("btnCrearReserva");

    if (btnCrearReserva) {
      btnCrearReserva.addEventListener("click", crearReserva);
      console.log("✅ Listener enganchado a #btnCrearReserva");
    }

    // 🔹 Función modular
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
        // 1️⃣ Buscar cliente por teléfono
        let resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
        let dataCliente = await resCliente.json();

        if (resCliente.ok && dataCliente.existe !== false) {
          clienteId = dataCliente.id_cliente;
        } else {
          // 2️⃣ Registrar cliente si no existe
          const nuevoClienteRes = await apiFetch("/clientes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              telefono,
              nombre: clienteNombre,
              direccion: origen,
              punto_referencia: "" // opcional
            })
          });

          const nuevoClienteData = await nuevoClienteRes.json();
          if (!nuevoClienteRes.ok) {
            mostrarToast("❌ Error al registrar cliente", "error");
            return;
          }
          clienteId = nuevoClienteData.id_cliente;
          mostrarToast(`✅ Cliente registrado con ID: ${clienteId}`, "success");
        }

        // 3️⃣ Crear la reserva
        const resReserva = await apiFetch("/reservas", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            cliente_id: clienteId,
            telefono,
            origen,
            destino,
            fecha,
            hora
          })
        });

        const dataReserva = await resReserva.json();

        if (resReserva.ok) {
          mostrarToast(`✅ Reserva creada con ID: ${dataReserva.id_reserva}`, "success");
          const modal = bootstrap.Modal.getInstance(document.getElementById("modalDespachoReserva"));
          modal.hide();
        } else {
          mostrarToast("❌ Error al crear la reserva", "error");
        }
      } catch (err) {
        console.error("Error:", err);
        mostrarToast("❌ No se pudo conectar al servidor", "error");
      }
    }


  ///////Búqueda de clientes en modal reserva////// 
  const inputTelefono = document.getElementById("resTelefono");
  const inputCliente = document.getElementById("resCliente");
  const inputOrigen = document.getElementById("resOrigen");

  if (inputTelefono) {
    inputTelefono.addEventListener("keydown", async (e) => {
      if (e.key === "Enter") {
        e.preventDefault();

        const telefono = inputTelefono.value.trim();
        const res = await apiFetch(`/clientes/telefono/${telefono}`);
        const data = await res.json();

        if (data.existe === false) {
          mostrarToast("⚠️ Cliente no registrado, ingresa datos manualmente", "warning");
          inputCliente.value = "";
          inputCliente.removeAttribute("readonly");
          inputOrigen.value = "";
          inputOrigen.removeAttribute("readonly");
        } else {
          inputCliente.value = data.nombre;
          inputCliente.setAttribute("readonly", "true");
          inputOrigen.value = data.direccion;
          inputOrigen.setAttribute("readonly", "true");
          mostrarToast(`✅ Cliente encontrado: ${data.nombre}`, "success");
        }
      }
    });
  }
  
    // Listener botón Múltiple
    const btnCrearDespachoMultiple = document.getElementById("btnCrearDespachoMultiple");
    if (btnCrearDespachoMultiple) {
      btnCrearDespachoMultiple.addEventListener("click", crearDespachoMultiple);
      console.log("✅ Listener enganchado a #btnCrearDespachoMultiple");
    }
  // -------------------------------
  // 📌 Sección: Reportes Generales
  // -------------------------------
  const btnGenerar = document.getElementById("btnGenerarReporte");
  if (btnGenerar) {
    btnGenerar.addEventListener("click", async () => {
      const inicio = document.getElementById("fechaInicio").value;
      const fin = document.getElementById("fechaFin").value;

      if (!inicio || !fin) {
        alert("Debes seleccionar fecha de inicio y fecha de fin");
        return;
      }
      if (inicio > fin) {
        alert("La fecha inicio no puede ser mayor que la fecha fin");
        return;
      }

      try {
        const res = await apiFetch(`/reportes?inicio=${inicio}&fin=${fin}`);
        const data = await res.json();
        const contenedor = document.getElementById("reporteResultado");
        contenedor.innerHTML = Array.isArray(data) && data.length > 0
          ? generarTablaGeneral(data)
          : "<p>No hay resultados en el rango seleccionado</p>";
      } catch (err) {
        console.error("❌ Error generando reporte:", err);
        alert("Error al generar reporte");
      }
    });
  }
  // -------------------------------
  // 📌 Sección: Reportes por Conductor
  // -------------------------------
  const btnConductores = document.getElementById("btnReporteConductores");
  if (btnConductores) {
    btnConductores.addEventListener("click", async () => {
      const inicio = document.getElementById("fechaInicio").value;
      const fin = document.getElementById("fechaFin").value;

      if (!inicio || !fin) {
        alert("Debes seleccionar fecha de inicio y fecha de fin");
        return;
      }
      if (inicio > fin) {
        alert("La fecha inicio no puede ser mayor que la fecha fin");
        return;
      }

      try {
        const res = await apiFetch(`/reportes/conductores?inicio=${inicio}&fin=${fin}`);
        const data = await res.json();
        const contenedor = document.getElementById("reporteConductoresResultado");
        contenedor.innerHTML = Array.isArray(data) && data.length > 0
          ? generarTablaConductores(data)
          : "<p>No hay resultados en el rango seleccionado</p>";
      } catch (err) {
        console.error("❌ Error generando reporte por conductor:", err);
        alert("Error al generar reporte por conductor");
      }
    });
  }

    // -------------------------------
    // 📌 Sección: Impresión de Reportes
    // -------------------------------
    const btnPrint = document.getElementById("btnPrint");
    if (btnPrint) {
      btnPrint.addEventListener("click", () => {
        const reporteGeneral = document.getElementById("reporteResultado");
        const reporteConductores = document.getElementById("reporteConductoresResultado");

        let contenido = "";
        if (reporteGeneral && reporteGeneral.innerHTML.trim() !== "") {
          contenido = reporteGeneral.innerHTML;
        } else if (reporteConductores && reporteConductores.innerHTML.trim() !== "") {
          contenido = reporteConductores.innerHTML;
        }

        if (contenido !== "") {
          const ventana = window.open("", "_blank");
          ventana.document.write(`
            <html>
              <head>
                <title>Reporte</title>
                <style>
                  body { font-family: Arial, sans-serif; margin: 1cm; }
                  h2 { text-align: center; }
                </style>
              </head>
              <body>
                ${contenido}
              </body>
            </html>
          `);
          ventana.document.close();
          ventana.print();
        } else {
          alert("No hay reporte generado para imprimir.");
        }
      });
    }

    // -------------------------------
    // 📌 Sección: Atajos de Teclado F1–F7
    // -------------------------------
    document.addEventListener("keydown", (e) => {
      if (e.key === "F1") { e.preventDefault(); abrirVista("despachos"); }
      if (e.key === "F2") { e.preventDefault(); abrirVista("despachosActivos"); }
      if (e.key === "F3") { e.preventDefault(); abrirVista("turnosActivos"); }
      if (e.key === "F4") { e.preventDefault(); abrirVista("autos"); }
      if (e.key === "F5") { e.preventDefault(); abrirVista("clientes"); }
      if (e.key === "F6") { e.preventDefault(); abrirVista("pagos"); }
      if (e.key === "F7") { e.preventDefault(); abrirVista("conductores"); }
    });

    // -------------------------------
    // 📌 Funciones auxiliares
    // -------------------------------
    function abrirVista(idVista) {
      document.querySelectorAll(".seccion").forEach(sec => sec.classList.add("hidden"));
      const vista = document.getElementById(idVista);
      if (vista) vista.classList.remove("hidden");
    }

    function generarTablaGeneral(data) {
      return `
        <div class="tabla-dinamica mb-4">
          <table class="border-collapse border w-full min-w-max">
            <thead class="bg-gray-100">
              <tr>
                <th class="border px-2 py-1">ID</th>
                <th class="border px-2 py-1">Cliente</th>
                <th class="border px-2 py-1">Conductor</th>
                <th class="border px-2 py-1">Origen</th>
                <th class="border px-2 py-1">Destino</th>
                <th class="border px-2 py-1">Fecha</th>
                <th class="border px-2 py-1">Tarifa</th>
              </tr>
            </thead>
            <tbody>
              ${data.map(r => `
                <tr>
                  <td class="border px-2 py-1">${r.id_despacho}</td>
                  <td class="border px-2 py-1">${r.cliente_nombre}</td>
                  <td class="border px-2 py-1">${r.conductor_codigo} - ${r.conductor_nombre} - ${r.auto_placa}</td>
                  <td class="border px-2 py-1">${r.origen}</td>
                  <td class="border px-2 py-1">${r.destino}</td>
                  <td class="border px-2 py-1">${r.fecha}</td>
                  <td class="border px-2 py-1">${r.tarifa}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function generarTablaConductores(data) {
      return `<table class="border-collapse border w-full">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-2 py-1">Conductor</th>
            <th class="border px-2 py-1">Total Servicios</th>
            <th class="border px-2 py-1">Total Tarifa</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(r => `
            <tr>
              <td class="border px-2 py-1">${r.conductor}</td>
              <td class="border px-2 py-1">${r.total_servicios}</td>
              <td class="border px-2 py-1">${r.total_tarifa.toFixed(2)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>`;
    }
  
});
// ✅ Listener global para tipoDespacho (fuera del contenedor)
document.addEventListener("change", (e) => {
  if (e.target && e.target.id === "tipoDespacho") {
    const valor = e.target.value;
    console.log("🌀 Cambio en tipoDespacho:", valor);

    if (valor === "multiple") {
      if (window.modalMultipleInstance) {
        console.log("🟢 Mostrando modal múltiple...");
        window.modalMultipleInstance.show();
      } else {
        console.error("❌ modalMultipleInstance no está definida");
      }
    }

    if (valor === "reserva") {
      if (window.modalReservaInstance) {
        console.log("🟢 Mostrando modal reserva...");
        window.modalReservaInstance.show();
      } else {
        console.error("❌ modalReservaInstance no está definida");
      }
    }
  }
  
});

