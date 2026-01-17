// ===============================
// dashboard.js
// Archivo central de lógica del dashboard
// ===============================

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
        const data = await apiFetch(`/reportes?inicio=${inicio}&fin=${fin}`);
        //const data = await res.json();
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
        const data = await apiFetch(`/reportes/conductores?inicio=${inicio}&fin=${fin}`);
        //const data = await res.json();
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
      // 1. Calculamos los totales recorriendo la data
      let totalServicios = 0;
      let totalMonto = 0;

      data.forEach(r => {
          totalServicios += parseInt(r.total_servicios) || 0;
          totalMonto += parseFloat(r.total_tarifa) || 0;
      });

      return `
        <div class="tabla-dinamica mb-4 shadow-sm border rounded-lg overflow-hidden">
          <table class="border-collapse border w-full min-w-max">
            <thead class="bg-gray-100 text-gray-700">
              <tr>
                <th class="border px-4 py-2 sticky top-0 bg-gray-100 text-left">Conductor</th>
                <th class="border px-4 py-2 sticky top-0 bg-gray-100 text-center">Total Servicios</th>
                <th class="border px-4 py-2 sticky top-0 bg-gray-100 text-right">Total Tarifa</th>
              </tr>
            </thead>
            <tbody class="text-gray-600">
              ${data.map(r => `
                <tr class="hover:bg-gray-50">
                  <td class="border px-4 py-1">${r.conductor}</td>
                  <td class="border px-4 py-1 text-center">${r.total_servicios}</td>
                  <td class="border px-4 py-1 text-right font-mono">${parseFloat(r.total_tarifa).toFixed(2)}</td>
                </tr>
              `).join("")}
            </tbody>
            <tfoot class="bg-gray-800 text-white font-bold">
              <tr>
                <td class="border px-4 py-2 text-right uppercase">Total General:</td>
                <td class="border px-4 py-2 text-center text-lg">${totalServicios}</td>
                <td class="border px-4 py-2 text-right text-lg font-mono">
                  ${totalMonto.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      `;
    }

   // -------------------------------
  // 📌 Sección: Reportes por Cliente
  // -------------------------------
  const btnCliente = document.getElementById("btnReporteCliente");
  if (btnCliente) {
    btnCliente.addEventListener("click", async () => {
      const telefono = document.getElementById("telefonoCliente").value;
      const token = localStorage.getItem("token");
      if (!telefono) {
        alert("Debes ingresar un número de teléfono");
        return;
      }

      try {
        const response = await fetch(`/reportes/cliente?telefono=${telefono}`, {
          headers: {
            "Authorization": `Bearer ${token}`,   // 👈 enviar token JWT
            "Content-Type": "application/json"
          }
        });

        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();

        const tbody = document.getElementById("tabla-reporte-cliente");
        tbody.innerHTML = "";

        if (Array.isArray(data) && data.length > 0) {
          data.forEach(item => {
            const row = `
              <tr>
                <td>${item.nombre_conductor}</td>
                <td>${item.origen}</td>
                <td>${item.destino}</td>
                <td>${item.ultima_fecha}</td>
              </tr>
            `;
            tbody.innerHTML += row;
          });
        } else {
          tbody.innerHTML = `<tr><td colspan="3">No se encontraron registros</td></tr>`;
        }
      } catch (err) {
        console.error("❌ Error generando reporte por cliente:", err);
        alert("Error al generar reporte por cliente");
      }

    });
  }
  
});

  
  // -------------------------------
  // 📌 Modal independiente: Teléfonos de Clientes
  // -------------------------------
  // Variable global para la página
  let paginaActual = 1;

  // Configurar los botones al cargar el DOM
  document.getElementById("btnPrev").onclick = () => {
      if (paginaActual > 1) cargarClientesTel(paginaActual - 1);
  };
  document.getElementById("btnNext").onclick = () => {
      cargarClientesTel(paginaActual + 1);
  };

  // Función de carga principal
  async function cargarClientesTel(page = 1) {
      paginaActual = page;
      try {
          const data = await apiFetch(`/clientes?page=${page}`);
          //const data = await res.json();
          
          renderTablaClientesTel(data.clientes);
          
          // Actualizar info y botones
          document.getElementById("infoPagina").textContent = `Página ${data.pagina_actual} de ${data.total_paginas}`;
          document.getElementById("btnPrev").disabled = (data.pagina_actual === 1);
          document.getElementById("btnNext").disabled = (data.pagina_actual === data.total_paginas);
          
          // Mostrar los controles (por si estaban ocultos)
          document.getElementById("controlesPaginacion").style.display = "flex";
      } catch (err) {
          console.error("❌ Error:", err);
      }
  }

  
 // 📌 Lógica del Buscador (Oculta la paginación)
document.querySelector("#buscarNombreTel").addEventListener("input", async (e) => {
    const query = e.target.value.trim();

    if (query.length === 0) {
        cargarClientesTel(1); 
        return;
    }

    if (query.length < 3) return;

    try {
        // Ocultamos la paginación mientras se busca
        document.getElementById("controlesPaginacion").style.display = "none";
        
        // CORRECCIÓN: apiFetch ya devuelve los datos procesados
        const filtrados = await apiFetch(`/clientes/search?q=${query}`);
        
        // Ahora pasamos 'filtrados' directamente a la tabla
        renderTablaClientesTel(filtrados);
        
    } catch (err) {
        console.error("❌ Error en búsqueda:", err);
    }
});
  

  function renderTablaClientesTel(clientes) {
    const tbody = document.querySelector('#tablaClientesTel tbody');
    tbody.innerHTML = ""; // Limpiar tabla anterior

    clientes.forEach((cliente, index) => {
      const tr = document.createElement("tr");
      tr.className = "cursor-pointer hover:bg-gray-100 border-b"; // Opcional: mejora visual

      // 📌 Cálculo de numeración correlativa
      // Si paginaActual es 1: (0 * 50) + (0 + 1) = 1
      // Si paginaActual es 2: (1 * 50) + (0 + 1) = 51
      const tdNum = document.createElement("td");
      tdNum.style.textAlign = "center";
      tdNum.style.padding = "8px";
      tdNum.textContent = ((paginaActual - 1) * 50) + (index + 1);

      const tdNombre = document.createElement("td");
      tdNombre.style.padding = "8px";
      tdNombre.textContent = cliente.nombre;

      const tdTelefono = document.createElement("td");
      tdTelefono.style.padding = "8px";
      tdTelefono.textContent = cliente.nro_telefono || cliente.telefono;

      const tdDireccion = document.createElement("td");
      tdDireccion.style.padding = "8px";
      // Aplicamos las clases de Tailwind: 
      // truncate: corta el texto con "..." 
      // max-w-xs: limita el ancho (aprox 320px)
      // cursor-help: para que el usuario sepa que hay más texto
      tdDireccion.className = "truncate max-w-xs cursor-help";
      // Guardamos la dirección completa en el atributo 'title' 
      // Así, cuando el operador ponga el mouse encima, verá la dirección completa en un globito
      tdDireccion.title = cliente.direccion || "Sin dirección";
      tdDireccion.textContent = cliente.direccion || "Sin dirección";

      tr.appendChild(tdNum);
      tr.appendChild(tdNombre);
      tr.appendChild(tdTelefono);
      tr.appendChild(tdDireccion);
      // Evento de selección
      tr.addEventListener("click", () => {
        seleccionarClienteTel(cliente);
        [...tbody.querySelectorAll("tr")].forEach(r => r.classList.remove("fila-seleccionada", "bg-blue-100"));
        tr.classList.add("fila-seleccionada", "bg-blue-100");
      });

      tbody.appendChild(tr);
    });
  }




  // En dashboard.js, dentro del evento input del buscador:
  // 📌 Búsqueda remota 


 function seleccionarClienteTel(cliente) {
    // 1. Guardamos el ID en el campo oculto (para el servidor)
    const inputId = document.querySelector("#cliIdTel");
    if (inputId) inputId.value = cliente.id_cliente || cliente.id;

    // 2. Mostramos los datos al operador (para la vista)
    document.querySelector("#cliNombreTel").value = cliente.nombre;
    document.querySelector("#cliTelefonoActualTel").value = cliente.nro_telefono || cliente.telefono;
    
    // 3. Limpiamos el campo de nuevo teléfono para que el operador escriba
    document.querySelector("#cliTelefonoNuevoTel").value = "";
    document.querySelector("#cliTelefonoNuevoTel").focus();
}
  

 function abrirModalTelefonosClientes() {
    document.getElementById("modalTelefonosClientes").classList.add("active");
    document.getElementById("modalTelefonosClientes").classList.remove("hidden");
    cargarClientesTel();
  }
  window.abrirModalTelefonosClientes = abrirModalTelefonosClientes;
  function cerrarModalTelefonosClientes() {
    document.getElementById("modalTelefonosClientes").classList.remove("active");
    document.getElementById("modalTelefonosClientes").classList.add("hidden");

  }
  window.cerrarModalTelefonosClientes = cerrarModalTelefonosClientes;

 document.getElementById("formEditarTelefono").addEventListener("submit", async e => {
    e.preventDefault();
    const idCliente = document.querySelector("#cliIdTel").value;
    const nombre = document.querySelector("#cliNombreTel").value;
    const nuevoTel = document.querySelector("#cliTelefonoNuevoTel").value;
    if (!idCliente) {
        alert("⚠️ Por favor, seleccione un cliente de la tabla primero.");
        return;
    }
    try {
        const res = await apiFetch(`/clientes/updateTelefono`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                id_cliente: idCliente, // Para la base de datos
                nombre: nombre,        // 👈 Para que la validación de Python no falle
                telefono: nuevoTel 
            })
        });
        
        alert("✅ Teléfono actualizado correctamente");
        cargarClientesTel();
    } catch (err) {
        console.error("❌ Error detectado:", err);
        
        let mensajeLimpio = "No se pudo actualizar el teléfono.";

        // Convertimos el error a string para analizarlo
        const errorStr = String(err);

        // Si el error contiene un JSON (buscamos la llave { )
        if (errorStr.includes('{')) {
            try {
                // Extraemos solo la parte que es JSON
                const inicioJson = errorStr.indexOf('{');
                const finJson = errorStr.lastIndexOf('}') + 1;
                const jsonRaw = errorStr.substring(inicioJson, finJson);
                
                const errorObj = JSON.parse(jsonRaw);
                
                // Usamos el mensaje que definiste en Python
                mensajeLimpio = errorObj.error || mensajeLimpio;
            } catch (e) {
                // Si falla el parseo, al menos quitamos el prefijo "Error: Error 400:"
                mensajeLimpio = errorStr.replace(/^Error: Error \d+: /g, "");
            }
        } else {
            mensajeLimpio = errorStr.replace(/^Error: Error \d+: /g, "");
        }

        // El alert ahora será profesional y limpio
        alert(`⚠️ Atención:\n${mensajeLimpio}`);
    }
});

  async function eliminarClienteTel() {
    // 1. Usar ID en lugar de nombre para precisión
    const idCliente = document.querySelector("#cliIdTel").value; 
    const nombre = document.querySelector("#cliNombreTel").value;

    if (!idCliente) {
      alert("⚠️ Selecciona un cliente primero.");
      return;
    }

    if (!confirm(`¿Seguro que deseas desactivar al cliente "${nombre}"?`)) {
      return;
    }

    try {
      // Cambiamos el concepto de 'delete' a 'desactivar'
      await apiFetch(`/clientes/api/clientes/${idCliente}/desactivar`, {
        method: "PATCH", // PATCH es mejor para actualizaciones parciales
        headers: { "Content-Type": "application/json" }
      });
      
      alert("✅ Cliente desactivado (se mantiene en el historial)");
      cargarClientesTel();
    } catch (err) {
      console.error("❌ Error al procesar:", err);
      alert("No se pudo desactivar el cliente.");
    }
  }
  window.eliminarClienteTel = eliminarClienteTel;
  
  // -------------------------------
  // 📌 Atajo de teclado Alt+T (solo admins)
  document.addEventListener("keydown", (e) => {
    if (e.altKey && e.key.toLowerCase() === "t") {
      e.preventDefault(); // evita cualquier acción por defecto
      const rol = localStorage.getItem('rol');
      if (rol && rol.toLowerCase() === 'admin') {
        abrirModalTelefonosClientes();
      } else {
        alert("⚠️ Solo los administradores pueden acceder a la gestión de teléfonos de clientes.");
      }
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

    async function registrarAuditoriaAcceso(evento) {
      const usuarioActivo = localStorage.getItem('usuario_nombre') || 'admin'; 

      try {
          // CAMBIO DE RUTA: ahora es /usuarios/log-acceso
          await apiFetch('/usuarios/log-acceso', {
              method: 'POST',
              body: JSON.stringify({
                  usuario: usuarioActivo,
                  evento: evento
              })
          });
      } catch (error) {
          console.error("Error de auditoría:", error);
      }
    }
  