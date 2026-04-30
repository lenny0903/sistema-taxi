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
    abrirVista('despachos') // ✅ usa la función unificada
  } else {
    abrirVista('clientesSection'); // ✅ usa la función unificada
    document.querySelectorAll('.menu-admin').forEach(el => el.style.display = 'none');
  }
  // Modifica tu listener de teclado para que cargue los datos
  document.addEventListener("keydown", (e) => {
      // ... otros atajos ...
      if (e.key === "F6") { 
        e.preventDefault(); 
        abrirVista("pagos"); 
        
        // 1. Cargamos el select de conductores
        cargarConductoresSelect(); 
        
        // 2. Cargamos el historial de pagos (la tabla de la derecha)
        if (window.cargarHistorialPagos) {
            cargarHistorialPagos();
        }
      }
  });
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
          // --- 1. CAPTURA DE VARIABLES (Esto es lo que faltaba) ---
          const inicio = document.getElementById("fechaInicio").value;
          const fin = document.getElementById("fechaFin").value;

          // --- 2. VALIDACIONES ---
          if (!inicio || !fin) {
              alert("Debes seleccionar fecha de inicio y fecha de fin");
              return;
          }
          if (inicio > fin) {
              alert("La fecha inicio no puede ser mayor que la fecha fin");
              return;
          }

          try {
              // Ahora 'inicio' y 'fin' ya existen y se pueden usar aquí
              const data = await apiFetch(`/reportes/conductores?inicio=${inicio}&fin=${fin}`);
              
              // Limpiamos otros contenedores
              if(document.getElementById("reporteResultado")) document.getElementById("reporteResultado").innerHTML = "";
              if(document.getElementById("tabla-reporte")) document.getElementById("tabla-reporte").innerHTML = "";
              if(document.getElementById("tabla-reporte-cliente")) document.getElementById("tabla-reporte-cliente").innerHTML = "";
              
              const contenedor = document.getElementById("reporteConductoresResultado");

              if (Array.isArray(data) && data.length > 0) {
                  // Inyectamos la tabla generada
                  contenedor.innerHTML = generarTablaConductores(data);
                  
                  // Scroll automático
                  contenedor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  
                  console.log("✅ Tabla de conductores visualizada");
              } else {
                  contenedor.innerHTML = "<p class='p-4 text-orange-600 bg-orange-50 rounded text-center'>No se encontraron servicios en este rango de fechas.</p>";
              }
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
   ///// Botón de impresión específico para reporte por conductores
  const btnPrintConductores = document.getElementById("btnPrintConductores");

    if (btnPrintConductores) {
      btnPrintConductores.addEventListener("click", () => {
        const reporteConductores = document.getElementById("reporteConductoresResultado");

        if (reporteConductores && reporteConductores.innerHTML.trim() !== "") {
          const contenido = reporteConductores.innerHTML;
          const ventana = window.open("", "_blank");

          ventana.document.write(`
            <html>
              <head>
                <title>Reporte de Servicios por Conductor</title>
                <style>
                  body { font-family: 'Segoe UI', Arial, sans-serif; margin: 1cm; color: #333; }
                  h2 { text-align: center; text-transform: uppercase; margin-bottom: 5px; }
                  .fecha { text-align: center; font-size: 11px; color: #666; margin-bottom: 20px; }
                  
                  /* Estilos para la tabla en la impresión */
                  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                  th, td { border: 1px solid #333; padding: 8px; font-size: 12px; }
                  
                  /* Alineaciones */
                  .text-center { text-align: center; }
                  .text-right { text-align: right; }
                  .text-left { text-align: left; }
                  .font-mono { font-family: monospace; }
                  
                  /* Colores para el PDF/Impresión */
                  thead { background-color: #f3f4f6; }
                  tfoot { background-color: #333; color: white; }
                  tr:nth-child(even) { background-color: #f9fafb; }
                </style>
              </head>
              <body>
                <h2>Línea de Taxis "Los Patriotas"</h2>
                <p class="fecha">Reporte de Servicios por Conductor<br>Generado el: ${new Date().toLocaleString()}</p>
                
                ${contenido}
                
                <div style="margin-top: 40px; border-top: 1px solid #ccc; pt-10px; font-size: 10px; text-align: center;">
                  Control Administrativo - San Cristóbal, Táchira
                </div>
              </body>
            </html>
          `);

          ventana.document.close();
          
          setTimeout(() => {
            ventana.print();
            ventana.close();
          }, 500);
        } else {
          alert("No hay datos en el reporte para imprimir.");
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
  let ventanaWhatsApp = null;
// --- Motor de Pagos ---
// --- MOTOR DE PAGOS (Control Interno vs Referencia) ---
  const fPagos = document.getElementById('formRegistrarPago');
  if (fPagos) {
      fPagos.addEventListener('submit', async (e) => {
          e.preventDefault();
          const formElement = e.target;

          // 1. CAPTURA DE DATOS PREVIA
          const d = Object.fromEntries(new FormData(formElement));
          const montoValor = document.getElementById('pago_monto')?.value || "0";
          const referenciaManual = d.referencia_pago || d.referencia || "s/r";

          try {
              // 2. REGISTRO EN EL SERVIDOR
              const resultado = await apiFetch('/pagos/registrar', { 
                  method: 'POST', 
                  body: JSON.stringify(d) 
              });

              console.log("Respuesta Servidor:", resultado);

              // 3. FORMATEO ÚNICO DEL CONTROL (00000)
              // Usamos una sola variable para todo el proceso
             const idDB = resultado.id || 0;
             const nroControlFinal = idDB.toString().padStart(5, '0');
             const montoReal = resultado.monto || "0"; // <--- Use lo que devuelve Python

              // 4. DATOS DE LA UNIDAD Y CONDUCTOR
              const selectConductor = formElement.querySelector('[name="conductor_id"]');
              const textoConductor = selectConductor ? selectConductor.options[selectConductor.selectedIndex].text : "S/N";
              const unidad = textoConductor.match(/\[Uni\s+(.*?)\]/)?.[1] || "S/N";
              const nombreConductor = textoConductor.split('] - ')[1] || textoConductor;
              const fecha = new Date().toLocaleString('es-VE', { 
                  day: '2-digit', month: '2-digit', year: 'numeric', 
                  hour: '2-digit', minute: '2-digit', hour12: true 
              });

              // 5. DISEÑO DEL SOPORTE .TXT
              const contenidoRecibo = 
                `ASOC. COOP. LOS PATRIOTAS DE TÁRIBA R.L\n` +
                `CONTROL INTERNO: ${nroControlFinal}\n` + 
                `RECIBO DE PAGO SEMANAL\n` +
                `--------------------------------------------\n` +
                `UNIDAD: ${unidad}\n` +
                `CONDUCTOR: ${nombreConductor}\n` +
                `MONTO: COP ${montoReal}\n` + // <--- Aquí ya no saldrá 0
                `METODO: ${d.metodo_pago || 'Efectivo'}\n` +
                `REF. PAGO: ${referenciaManual}\n` + 
                `FECHA: ${fecha}\n` +
                `--------------------------------------------\n` +
                `Comprobante generado por el sistema de gestión.`;
              // 6. DESCARGA DEL ARCHIVO
              const blob = new Blob([contenidoRecibo], { type: 'text/plain' });
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              // El nombre del archivo ahora coincide con el contenido
              a.download = `Recibo_Ctrl_${nroControlFinal}_Uni_${unidad}.txt`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              window.URL.revokeObjectURL(url);

              // Alerta a la administradora con el número formateado
              alert(`✅ Registrado con Control Interno: ${nroControlFinal}`);

              // 7. RESET Y RECARGA
              formElement.reset();
              if (window.cargarConductoresSelect) window.cargarConductoresSelect();
              if (window.cargarEstadoSemana) window.cargarEstadoSemana();

          } catch (err) {
              console.error("Error:", err);
              alert("Error al procesar el pago o generar el soporte.");
          }
      });
  }  
});  
  // -------------------------------
  // 📌 Funciones auxiliares
  // -------------------------------
  
 function generarTablaGeneral(data) {
    return `
      <div class="tabla-dinamica mb-4">
        <table class="border-collapse border w-full min-w-max">
          <thead class="bg-gray-100">
            <tr>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">ID</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">#</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Cliente</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Conductor</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Origen</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Destino</th>
              <th class="border px-2 py-1 sticky top-0 bg-gray-100">Fecha</th>
              
            </tr>
          </thead>
          <tbody>
           ${data.map((r, index) => `
              <tr>
                <td class="border px-2 py-1">${r.id_despacho}</td>
                <td class="border px-2 py-1 font-bold text-center">${index + 1}</td>
                <td class="border px-2 py-1 text-sm">
                    <div class="font-semibold text-gray-900">${r.cliente_nombre}</div>
                    <div class="text-xs text-gray-500">${r.cliente_telefono}</div> 
                </td>
                <td class="border px-2 py-1 text-xs">
                    ${r.conductor_codigo} - ${r.conductor_nombre} <br>
                    <span class="text-[10px] font-mono bg-gray-200 px-1 rounded">${r.auto_placa}</span>
                </td>

                <td class="border px-2 py-1 text-xs" style="max-width: 200px; word-wrap: break-word; white-space: normal;">
                    ${r.origen}
                </td>
                <td class="border px-2 py-1 text-xs" style="max-width: 200px; word-wrap: break-word; white-space: normal;">
                    ${r.destino}
                </td>
                <td class="border px-2 py-1 text-[10px] leading-tight">${r.fecha}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

    function generarTablaConductores(data) {
      let totalServicios = 0;
      let totalMonto = 0;

      // 1. Calculamos totales
      data.forEach(r => {
          totalServicios += parseInt(r.total_servicios) || 0;
          totalMonto += parseFloat(String(r.total_tarifa || "0").replace(',', '.')) || 0;
      });

      // 2. Generamos las filas de los conductores
      let filas = data.map(r => {
          const vTarifa = parseFloat(String(r.total_tarifa || "0").replace(',', '.')) || 0;
          return `
              <tr style="border-bottom: 1px solid #dee2e6;">
                  <td style="padding: 8px; text-align: left;">${r.conductor}</td>
                  <td style="padding: 8px; text-align: center;">${r.total_servicios}</td>
                  <td style="padding: 8px; text-align: right; font-family: monospace;">
                      ${vTarifa.toLocaleString('es-VE', { minimumFractionDigits: 2 })}
                  </td>
              </tr>
          `;
      }).join("");

      // 3. AGREGAMOS LA FILA DE TOTALES COMO UNA FILA MÁS (Sin usar TFOOT)
      const filaTotal = `
          <tr style="background-color: #1f2937; color: white; font-weight: bold;">
              <td style="padding: 10px; text-align: right;">TOTAL GENERAL:</td>
              <td style="padding: 10px; text-align: center; font-size: 1.1em;">${totalServicios}</td>
              <td style="padding: 10px; text-align: right; font-size: 1.1em; font-family: monospace;">
                  ${totalMonto.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </td>
          </tr>
      `;

      return `
          <div style="width: 100%; overflow-x: auto; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 8px;">
              <table style="width: 100%; border-collapse: collapse; background-color: white;">
                  <thead>
                      <tr style="background-color: #f3f4f6; border-bottom: 2px solid #ccc;">
                          <th style="padding: 10px; text-align: left;">Conductor</th>
                          <th style="padding: 10px; text-align: center;">Total Servicios</th>
                          <th style="padding: 10px; text-align: right;">Total Tarifa</th>
                      </tr>
                  </thead>
                  <tbody>
                      ${filas}
                      ${filaTotal}
                  </tbody>
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
      const telefonoInput = document.getElementById("telefonoCliente");
      if (!telefonoInput) return;

      const telefono = telefonoInput.value.trim();
      const token = localStorage.getItem("token");

      // VALIDACIONES (Alineadas correctamente)
      if (!token) {
        alert("Sesión expirada. Por favor, vuelve a iniciar sesión.");
        window.location.href = "/login";
        return;
      }

      if (!telefono) {
        alert("Debes ingresar un número de teléfono");
        return;
      }

      try {
        const response = await fetch(`/reportes/cliente?telefono=${telefono}`, {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        });

        if (response.status === 401) {
          throw new Error("No autorizado: Tu sesión ha caducado.");
        }

        if (!response.ok) {
          throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();
        const tbody = document.getElementById("tabla-reporte-cliente");
        let filas = ""; 

        if (Array.isArray(data) && data.length > 0) {
          data.forEach(item => {
            filas += `
              <tr>
                <td>${item.nombre_conductor}</td>
                <td>${item.origen}</td>
                <td>${item.destino}</td>
                <td>${item.ultima_fecha}</td>
              </tr>`;
          });
          tbody.innerHTML = filas;
        } else {
          tbody.innerHTML = `<tr><td colspan="4" class="text-center">No se encontraron registros</td></tr>`;
        }
      } catch (err) {
        console.error("❌ Error:", err);
        alert(err.message);
      }
    }); // Cierre del listener
  } // Cierre del if  
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
    if (!tbody) return;
    tbody.innerHTML = ""; 

    clientes.forEach((cliente, index) => {
      const tr = document.createElement("tr");
      // Añadimos una transición suave para el hover
      tr.className = "cursor-pointer hover:bg-gray-100 border-b transition-colors";

      // 1. Numeración correlativa real
      const num = ((paginaActual - 1) * 50) + (index + 1);

      // 2. Construcción limpia con Template Literals
      tr.innerHTML = `
        <td class="p-2 text-center text-gray-500">${num}</td>
        <td class="p-2 font-medium">${cliente.nombre}</td>
        <td class="p-2 font-mono">${cliente.nro_telefono || cliente.telefono || 'S/N'}</td>
        <td class="p-2 truncate max-w-xs cursor-help" title="${cliente.direccion || 'Sin dirección'}">
          ${cliente.direccion || "Sin dirección"}
        </td>
      `;

      // 3. Evento de selección con feedback visual
      tr.addEventListener("click", () => {
        seleccionarClienteTel(cliente);
        // Limpiamos selección previa y marcamos la nueva
        tbody.querySelectorAll("tr").forEach(r => r.classList.remove("bg-blue-100", "font-bold"));
        tr.classList.add("bg-blue-100", "font-bold");
      });

      tbody.appendChild(tr);
    });
  }

  // En dashboard.js, dentro del evento input del buscador:
  // 📌 Búsqueda remota 


 function seleccionarClienteTel(cliente) {
    const inputId = document.querySelector("#cliIdTel");
    const inputNombre = document.querySelector("#cliNombreTel");
    const inputTelActual = document.querySelector("#cliTelefonoActualTel");
    const inputNuevo = document.querySelector("#cliTelefonoNuevoTel");

    if (inputId) inputId.value = cliente.id_cliente || cliente.id;
    if (inputNombre) inputNombre.value = cliente.nombre;
    if (inputTelActual) inputTelActual.value = cliente.nro_telefono || cliente.telefono;
    if (inputNuevo) {
      inputNuevo.value = "";
      inputNuevo.focus();
    }
  }
  window.seleccionarClienteTel = seleccionarClienteTel;
  

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
    const idCliente = document.querySelector("#cliIdTel").value; 
    const nombre = document.querySelector("#cliNombreTel").value;

    if (!idCliente) {
      alert("⚠️ Selecciona un cliente de la tabla primero.");
      return;
    }

    if (!confirm(`¿Estás seguro de que deseas eliminar/desactivar a "${nombre}"?`)) {
      return;
    }

    try {
      const response = await apiFetch(`/clientes/${idCliente}`, {
          method: "DELETE"
      });
      
      // Informamos según la lógica de historial que hicimos
      alert(response.mensaje || "✅ Operación realizada con éxito.");

      // LIMPIEZA CORRECTA SEGÚN TU HTML:
      document.querySelector("#cliIdTel").value = "";
      document.querySelector("#cliNombreTel").value = "";
      document.querySelector("#cliTelefonoActualTel").value = "";
      document.querySelector("#cliTelefonoNuevoTel").value = "";
      
      // Opcional: Limpiar también el buscador de arriba
      if (document.querySelector("#buscarNombreTel")) {
          document.querySelector("#buscarNombreTel").value = "";
      }

      // Recargar la tabla para que el cliente desaparezca de la lista
      if (typeof cargarClientesTel === 'function') {
          cargarClientesTel(); 
      }
      
    } catch (err) {
      console.error("❌ Error al procesar:", err);
      alert("No se pudo completar la operación.");
    }
  }
  window.eliminarClienteTel = eliminarClienteTel;
   

   function abrirVista(idVista) {
      // 1. Ocultar usando la clase REAL que tienes en el HTML (seccion-contenido)
      document.querySelectorAll(".seccion-contenido").forEach(sec => {
          sec.classList.add("hidden");
      });
      
      // 2. Mostrar la sección solicitada
      const vista = document.getElementById(idVista);
      if (vista) {
          vista.classList.remove("hidden");
          console.log(`✅ Vista abierta: ${idVista}`);

          // 🚀 EL GATILLO: Normalizamos a minúsculas por seguridad
          if (idVista.toLowerCase() === 'pagos') { 
              console.log("⚙️ Ejecutando recarga de datos para 'Los Patriotas'...");
              
              // Verificamos que las funciones existan antes de llamar
              if (typeof window.cargarConductoresSelect === 'function') {
                  window.cargarConductoresSelect();
              }

              if (typeof window.cargarHistorialPagos === 'function') {
                  window.cargarHistorialPagos();
              }

              if (typeof window.cargarEstadoSemana === 'function') {
                  window.cargarEstadoSemana();
              }
              
          }
      } else {
          console.warn(`⚠️ Ojo: No encontré el ID '${idVista}' en el HTML`);
      }
    }
  window.abrirVista = abrirVista;

   async function registrarAuditoriaAcceso(evento) {
    const usuarioActivo = localStorage.getItem('usuario_nombre') || 'admin'; 
    try {
      await apiFetch('/usuarios/log-acceso', {
        method: 'POST',
        body: JSON.stringify({ usuario: usuarioActivo, evento: evento })
      });
    } catch (error) {
      console.error("Error de auditoría:", error);
    }
  }
  window.registrarAuditoriaAcceso = registrarAuditoriaAcceso;
  window.cargarConductoresSelect = async function() {
    const select = document.getElementById('pago_conductor_id');
    if (!select) {
        console.error("❌ No se encontró el select 'pago_conductor_id'");
        return;
    }

    try {
        console.log("📡 Solicitando conductores a la API...");
        const data = await apiFetch('/conductores/disponibles_conductores');
        
        select.innerHTML = '<option value="">Seleccione Unidad / Conductor...</option>';

        if (Array.isArray(data) && data.length > 0) {
            data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id_conductor;
                opt.textContent = `[Uni ${c.codigo}] - ${c.nombre}`;
                select.appendChild(opt);
            });
            console.log("✅ Lista de conductores cargada con éxito");
        } else {
            console.warn("⚠️ No se recibieron conductores disponibles");
            select.innerHTML = '<option value="">No hay conductores disponibles</option>';
        }
    } catch (err) {
        console.error("❌ Error en la petición:", err);
    }
  };
  window.cargarHistorialPagos = async function() {
    const tbody = document.getElementById('tabla_historial_pagos');
    
    if (!tbody) {
        console.error("❌ ERROR: No existe el ID 'tabla_historial_pagos' en el HTML.");
        return;
    }

    try {
        console.log("📡 Intentando conectar con /pagos/recientes...");
        const pagos = await apiFetch('/pagos/recientes');
        
        console.log("📦 Datos recibidos del servidor:", pagos);

        if (!pagos || pagos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center">No hay pagos en la base de datos.</td></tr>';
            return;
        }

        tbody.innerHTML = pagos.map(p => `
            <tr class="border-b hover:bg-gray-50">
                <td class="px-4 py-2 text-sm">${p.fecha}</td>
                <td class="px-4 py-2 font-medium">${p.conductor}</td>
                <td class="px-4 py-2 text-blue-600">${p.semana}</td>
                <td class="p-2 text-right font-bold text-green-700">
                    ${Number(p.monto).toLocaleString('es-VE')} COP
                </td>
                <td class="px-4 py-2 text-gray-500 text-xs">${p.ref || 's/r'}</td>
            </tr>
        `).join('');
        
        console.log("✅ Tabla renderizada con éxito.");
    } catch (err) {
        console.error("❌ ERROR en la petición:", err);
        tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-red-500">Error de conexión.</td></tr>';
    }
 };
 
// ================================================================
// SECCIÓN: CONTROL DE ESTADO SEMANAL Y SALDOS (VERSIÓN ÚNICA)
// ================================================================

async function cargarEstadoSemana() {
    const tbody = document.getElementById('tablaEstadoPagos');
    if (!tbody) return;

    try {
        console.log("📡 Consultando solvencia semanal...");
        const conductores = await apiFetch('/pagos/estado_semana');
        
        // Limpiar tabla
        tbody.innerHTML = '';

        if (!conductores || conductores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">No hay datos para esta semana.</td></tr>';
            return;
        }

        conductores.forEach(c => {
            // Usamos las llaves que confirmamos en su consola
            const idValue = c.id_conductor; 
            const nombreValue = c.conductor;

            const fila = `
                <tr class="border-b hover:bg-gray-50">
                    <td class="p-2 text-center font-mono font-bold">${c.unidad}</td>
                    <td class="p-2 text-sm">${nombreValue}</td>
                    <td class="p-2 text-right font-mono font-bold">$${c.saldo}</td>
                    <td class="p-2 text-center">${c.status_html}</td>
                    <td class="p-2 text-center">
                        ${!c.pagado ? 
                            `<button onclick="prepararCobro('${idValue}', '${nombreValue}')"
                                class="bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-bold px-3 py-1.5 rounded">
                                COBRAR
                            </button>` 
                            : '<span class="text-green-600 font-bold text-xs">✅ SOLVENTE</span>'}
                    </td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', fila);
        });
    } catch (error) {
        console.error('❌ Error al cargar estado_semana:', error);
    }
}

// Hacerla global
window.cargarEstadoSemana = cargarEstadoSemana;

window.prepararCobro = function(id, nombre) {
    console.log("PUENTE ACTIVADO -> ID:", id, "Nombre:", nombre);
    
    const inputId = document.getElementById('modal_conductor_id');
    const elementoNombre = document.getElementById('modal_nombre_conductor');
    
    if (inputId) inputId.value = id;
    
    if (elementoNombre) {
        if (elementoNombre.tagName === 'INPUT') {
            elementoNombre.value = nombre;
        } else {
            elementoNombre.innerText = nombre;
        }
    }
    
    document.getElementById('modalCargaInicial').classList.remove('hidden');
};

// El resto de sus funciones (cerrarModalCarga y onsubmit) se mantienen igual abajo...

window.cerrarModalCarga = function() {
    document.getElementById('modalCargaInicial').classList.add('hidden');
    document.getElementById('formCargaInicial').reset();
};

// Manejador del envío del formulario del Modal
document.getElementById('formCargaInicial').onsubmit = async (e) => {
    e.preventDefault();
    
    const datos = {
        conductor_id: document.getElementById('modal_conductor_id').value,
        monto: document.getElementById('modal_monto').value,
        referencia_pago: document.getElementById('modal_referencia').value
    };

    try {
        const response = await fetch('/pagos/carga_inicial_pagos', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}` // Si usa JWT
            },
            body: JSON.stringify(datos)
        });

        if (response.ok) {
            alert('¡Nivelación exitosa!');
            
            // 1. Cerramos el modal de inmediato
            cerrarModalCarga();
            
            // 2. Refrescamos la tabla de solvencia sin recargar la página
            // Esta es la función que unificamos hace un momento
            if (typeof cargarEstadoSemana === 'function') {
                cargarEstadoSemana();
            }

            // 3. Opcional: Si tiene la tabla de "Pagos Recientes" abajo, la refrescamos también
            if (typeof cargarPagosRecientes === 'function') {
                cargarPagosRecientes();
            }

            console.log("✅ Vista de pagos actualizada mediante AJAX.");
        } else {
            const err = await response.json();
            alert('Error: ' + (err.error || 'No se pudo procesar el pago'));
        }
    } catch (error) {
        console.error('Error en la carga:', error);
    }
};
