// ===============================
// dashboard.js
// Archivo central de lógica del dashboard
// ===============================

document.addEventListener("DOMContentLoaded", () => {

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
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">ID</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Cliente</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Conductor</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Origen</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Destino</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Fecha</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Tarifa</th>
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
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem('token');
  const rol = localStorage.getItem('rol');

  if (!token) {
    window.location.href = '/index.html';
    return;
  }

  const roleSpan = document.getElementById('userRole');
  if (roleSpan) {
    roleSpan.textContent = `Rol: ${rol}`;
  }

  if (rol && rol.toLowerCase() === 'admin') {
    mostrarSeccion('despachos'); // ✅ usa la función unificada
  } else {
    mostrarSeccion('clientesSection'); // ✅ usa la función unificada
    document.querySelectorAll('.menu-admin').forEach(el => el.style.display = 'none');
  }
});

function abrirVista(idVista) {
  // Ocultar todas las secciones
  document.querySelectorAll(".seccion").forEach(sec => sec.classList.add("hidden"));

  // Mostrar la sección solicitada
  const vista = document.getElementById(idVista);
  if (vista) {
    vista.classList.remove("hidden");
    console.log(`✅ Vista abierta: ${idVista}`);
  } else {
    console.warn(`⚠️ Sección '${idVista}' no encontrada en el DOM`);
  }
}

