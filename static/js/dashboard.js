// ===============================
// dashboard.js
// Archivo central de lógica del dashboard
// ===============================
// --- GUARDIA DE SEGURIDAD GLOBAL ---
window.socket = io();
(function() {
    const rol = (localStorage.getItem("rol") || "").trim().toLowerCase();
    
    // Si el rol es operador, hackeamos el historial y la carga inicial
    if (rol === 'operador') {
        const observer = new MutationObserver(() => {
            const clientesSec = document.getElementById('clientesSection');
            if (clientesSec && !clientesSec.classList.contains('hidden')) {
                console.warn("🚫 Intento de carga ilegal detectado. Bloqueando...");
                clientesSec.classList.add('hidden');
                clientesSec.style.display = 'none';
                mostrarSeccion('despachos'); // Redirección forzada
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();
document.addEventListener("DOMContentLoaded", () => {
    // --- AQUÍ PEGAS TU CÓDIGO NUEVO ---
    const switchGlobal = document.getElementById("switchGlobalWhatsApp");
    const textGlobal = document.getElementById("textGlobalWhatsApp");
    const bgGlobal = document.getElementById("bgGlobalWhatsApp");
    const circleGlobal = document.getElementById("circleGlobalWhatsApp");

    function actualizarEstiloGlobal(activo) {
        if (!bgGlobal || !circleGlobal || !textGlobal) return;
        if (activo) {
            textGlobal.innerText = "🤖 API: AUTOMÁTICA";
            bgGlobal.className = "w-9 h-5 bg-green-600 rounded-full transition-colors relative";
            circleGlobal.className = "absolute top-[2px] left-[2px] bg-white rounded-full h-3.5 w-3.5 transition-transform translate-x-4";
        } else {
            textGlobal.innerText = "👤 API: MANUAL";
            bgGlobal.className = "w-9 h-5 bg-gray-300 rounded-full transition-colors relative";
            circleGlobal.className = "absolute top-[2px] left-[2px] bg-white rounded-full h-3.5 w-3.5 transition-transform translate-x-0";
        }
    }

    if (switchGlobal) {
        const estadoGuardado = localStorage.getItem("global_whatsapp_activo") !== "false";
        switchGlobal.checked = estadoGuardado;
        actualizarEstiloGlobal(estadoGuardado);

        switchGlobal.addEventListener("change", (e) => {
            const activo = e.target.checked;
            localStorage.setItem("global_whatsapp_activo", activo);
            actualizarEstiloGlobal(activo);
            if (typeof mostrarToast === 'function') {
                mostrarToast(activo ? "🤖 WhatsApp en modo Automático" : "👤 WhatsApp en modo Manual", "info");
            }
        });
    }

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
        abrirVista('despachos'); 
    } else {
        // CAMBIO: Abre 'despachos' o cualquier vista pública para el operador
        abrirVista('despachos'); 
        
        // Ocultar elementos admin
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
  // 📌 Sección: Reporte de Pagos (Contabilidad)
  // -------------------------------
  const btnReportePagos = document.getElementById("btnReportePagos");

  if (btnReportePagos) {
        btnReportePagos.addEventListener("click", async () => {
            // 1. CAPTURA DE FECHAS
            const inicio = document.getElementById("fechaInicio").value;
            const fin = document.getElementById("fechaFin").value;

            // 2. VALIDACIONES
            if (!inicio || !fin) {
                alert("Debes seleccionar fecha de inicio y fecha de fin para el cierre de caja");
                return;
            }

            try {
                // LLAMADA AL BACKEND (Ruta que definimos en reportes.py)
                const data = await apiFetch(`/reportes/pagos?inicio=${inicio}&fin=${fin}`);
                
                // Limpiamos los otros contenedores de reportes para no confundir
                ["reporteResultado", "reporteConductoresResultado", "reporte-container", "reporteClienteResultado"]
                .forEach(id => {
                    const el = document.getElementById(id);
                    if(el) el.innerHTML = "";
                });

                const contenedorTabla = document.getElementById("tbodyPagosReporte");
                const contenedorResumen = document.getElementById("resumenCaja");

                if (data && data.pagos && data.pagos.length > 0) {
                contenedorTabla.innerHTML = data.pagos.map(p => {
                    // Ahora usamos la propiedad booleana que viene del backend
                    const esExoneracion = p.es_exoneracion; 
                    const montoSaldo = esExoneracion ? 0 : p.monto;
                    
                    return `
                        <tr class="text-sm hover:bg-gray-50">
                            <td class="border p-2">${p.fecha_pago}</td>
                            <td class="border p-2 font-bold">${p.numero_unidad}</td>
                            <td class="border p-2">${p.conductor}</td>
                            <td class="border p-2 text-right">${p.monto.toLocaleString()}</td> 
                            <td class="border p-2 text-right font-bold ${esExoneracion ? 'text-green-600' : 'text-red-600'}">
                                ${montoSaldo.toLocaleString()}
                            </td> 
                            <td class="border p-2 text-center">
                                <span class="px-2 py-1 rounded text-xs ${esExoneracion ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}">
                                    ${p.metodo_pago}
                                </span>
                            </td>
                            <td class="border p-2 text-xs text-gray-500">${p.referencia || '-'}</td>
                        </tr>
                    `;
                }).join('');

                // Actualizamos el resumen con los datos calculados en el backend
                // Nota: Como ahora el backend envía 'efectivo' y 'total_general' limpios, 
                // úsalos directamente para evitar errores.
                document.getElementById("totalEfectivo").innerText = data.totales.efectivo.toLocaleString() + " COP";
                document.getElementById("totalExonerado").innerText = data.totales.exonerado.toLocaleString() + " COP";
                // Si tu resumen tiene 'transferencia' y quieres mostrarlo, asegúrate que el backend lo envíe
                if(document.getElementById("totalTransf")) {
                    document.getElementById("totalTransf").innerText = (data.totales.transferencia || 0).toLocaleString() + " COP";
                }
                
                document.getElementById("totalGeneral").innerText = data.totales.total_general.toLocaleString() + " COP";

                // Mostramos la tabla y el resumen (quitamos 'hidden')
                contenedorResumen.classList.remove("hidden");
                document.getElementById("tablaPagosReporte").classList.remove("hidden");
                
                // Scroll suave al resultado
                document.getElementById("reportePagosResultado").scrollIntoView({ behavior: 'smooth' });
                
                } else {
                alert("No se encontraron pagos en el rango seleccionado.");
                contenedorResumen.classList.add("hidden");
                document.getElementById("tablaPagosReporte").classList.add("hidden");
                }
            } catch (err) {
                console.error("❌ Error en reporte de contabilidad:", err);
                alert("Error al conectar con el servidor de reportes");
            }
        });
    }
   

    // Llámela dentro de su DOMContentLoaded o cuando cambie de vista a 'reportes'
    //restringirAccesoPorRol();
  // -------------------------------
  // 📌 Sección: Atajos de Teclado F1–F7
  // -------------------------------
  document.addEventListener("keydown", (e) => {
    if (e.key === "F1") { e.preventDefault(); abrirVista("despachos"); }
    if (e.key === "F2") { e.preventDefault(); abrirVista("despachosActivos"); }
    if (e.key === "F3") { e.preventDefault(); abrirVista("turnosActivos"); }
    if (e.key === "F4") { e.preventDefault(); abrirVista("autos"); }
    //if (e.key === "F5") { e.preventDefault(); abrirVista("clientes"); }
    if (e.key === "F6") { e.preventDefault(); abrirVista("pagos"); }
    if (e.key === "F7") { e.preventDefault(); abrirVista("conductores"); }
  });
  let ventanaWhatsApp = null;
 // --- Motor de Pagos ---
 // --- MOTOR DE PAGOS (Control Interno vs Referencia) ---
  // --- LÓGICA DE INTERFAZ PARA EXONERACIONES ---
    // =========================================================================
    // 📡 1. ESCUCHA ACTIVA DEL CONDUCTOR PARA CARGAR SUS SEMANAS PENDIENTES
    // =========================================================================
    const selectConductor = document.getElementById('pago_conductor_id');
    const selectSemana = document.getElementById('reg_semana_pago');

    if (selectConductor && selectSemana) {
        selectConductor.addEventListener('change', async function() {
            const conductorId = this.value;

            if (!conductorId) {
                selectSemana.innerHTML = '<option value="">-- Seleccione primero un conductor --</option>';
                selectSemana.disabled = true;
                return;
            }

            selectSemana.innerHTML = '<option value="">⏳ Consultando deudas en tiempo real...</option>';
            selectSemana.disabled = true;

            try {
                // Consultamos al backend las semanas en mora de este conductor
                const response = await apiFetch(`/pagos/semanas_pendientes/${conductorId}`, { method: 'GET' });
                selectSemana.innerHTML = ''; 

               if (response.semanas && response.semanas.length > 0) {
                    response.semanas.forEach(semanaStr => {
                        // 💡 Limpieza limpia: maneja formatos con "W" o con guion simple (Ej: "2026-21" -> "21")
                        let numSemana = semanaStr;
                        if (semanaStr.includes('-W')) numSemana = semanaStr.split('-W')[1];
                        else if (semanaStr.includes('-')) numSemana = semanaStr.split('-')[1];

                        const option = document.createElement('option');
                        option.value = semanaStr; // Viaja limpio a Flask (Ej: "2026-21")
                        
                        // 🎯 REGLA ADAPTATIVA: Si el backend envía semanas futuras o el saldo es a favor
                        // Cambiamos la etiqueta para que la administradora sepa qué está haciendo
                        // Si la semana devuelta es mayor que la de corte actual o si es una predicción:
                        if (response.es_adelanto) { // O una lógica equivalente basada en la respuesta
                            option.innerText = `Semana ${numSemana} (Cuota Adelantada)`;
                        } else {
                            option.innerText = `Semana ${numSemana} (Pendiente)`;
                        }
                        
                        selectSemana.appendChild(option);
                    });
                    selectSemana.disabled = false;
                } else {
                    // 🎯 Respaldo de seguridad si el array llega vacío
                    selectSemana.innerHTML = '<option value="">✔️ CONDUCTOR COMPLETAMENTE SOLVENTE</option>';
                    selectSemana.disabled = true;
                }
            } catch (error) {
                console.error("❌ Error al recuperar semanas para taquilla:", error);
                selectSemana.innerHTML = '<option value="">⚠️ Error al cargar semanas pendientes</option>';
                selectSemana.disabled = true;
            }
        });
    }

    // =========================================================================
    // 🎨 2. REACTIVIDAD DEL BOTÓN SEGÚN EL TIPO DE NOVEDAD
    // =========================================================================
    const selectNovedad = document.getElementById('tipo_novedad');
    if (selectNovedad) {
        selectNovedad.addEventListener('change', (e) => {
            const esExoneracion = e.target.value !== 'PAGO_NORMAL';
            const seccionPago = document.getElementById('seccion_pago_real');
            const btn = document.querySelector('#formRegistrarPago button[type="submit"]');
            
            if (esExoneracion) {
                if (seccionPago) seccionPago.classList.add('hidden');
                btn.classList.replace('bg-blue-600', 'bg-purple-600');
                btn.classList.replace('hover:bg-blue-700', 'hover:bg-purple-700');
                btn.innerText = `Registrar Exoneración (${e.target.options[e.target.selectedIndex].text})`;
            } else {
                if (seccionPago) seccionPago.classList.remove('hidden');
                btn.classList.replace('bg-purple-600', 'bg-blue-600');
                btn.classList.replace('hover:bg-purple-700', 'hover:bg-blue-700');
                btn.innerText = 'Procesar Pago (40.000 COP)';
            }
        });
    }

    // =========================================================================
    // 🧠 3. ENVÍO, PROCESAMIENTO CONTABLE Y GENERACIÓN DE RECIBO
    // =========================================================================
    const fPagos = document.getElementById('formRegistrarPago');
    if (fPagos) {
        fPagos.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formElement = e.target;

            // Captura inicial de datos desde el formulario
            const d = Object.fromEntries(new FormData(formElement));
            
            // 🚨 ADUANA DE SEGURIDAD CRUCIAL EN EL FRONTEND
            if (!d.semana_anio) {
                alert("❌ Error: No se puede procesar el pago porque el conductor no posee semanas pendientes.");
                return;
            }

            const referenciaManual = d.referencia || "s/r";
            const novedadTexto = selectNovedad ? selectNovedad.options[selectNovedad.selectedIndex].text : "PAGO NORMAL";
            const esExoneracion = d.tipo_novedad && d.tipo_novedad !== 'PAGO_NORMAL';
            
            // Limpiamos el texto de la semana para el recibo (Ej: de "2026-W18" nos quedamos con "18")
            const numeroSemanaRecibo = d.semana_anio.includes('-W') ? d.semana_anio.split('-W')[1] : d.semana_anio;

            try {
                // 📡 REGISTRO EN EL SERVIDOR (Ruta específica de taquilla que procesa la fila exacta)
                const resultado = await apiFetch('/pagos/registrar_pago_ordinario', { 
                    method: 'POST', 
                    body: JSON.stringify(d) 
                });

                console.log("Respuesta Servidor:", resultado);

                const idDB = resultado.id || 0;
                const nroControlFinal = idDB.toString().padStart(5, '0');
                const montoReal = resultado.monto || "0"; 

                // Datos de la unidad y conductor
                const selectConductorNodo = formElement.querySelector('[name="conductor_id"]');
                const textoConductor = selectConductorNodo ? selectConductorNodo.options[selectConductorNodo.selectedIndex].text : "S/N";
                const unidad = textoConductor.match(/\[Uni\s+(.*?)\]/)?.[1] || "S/N";
                const nombreConductor = textoConductor.split('] - ')[1] || textoConductor;
                const fecha = new Date().toLocaleString('es-VE', { 
                    day: '2-digit', month: '2-digit', year: 'numeric', 
                    hour: '2-digit', minute: '2-digit', hour12: true 
                });

                // Formateo del diseño del soporte .txt incorporando la semana auditada
                const tituloRecibo = esExoneracion ? `COMPROBANTE DE EXONERACIÓN` : `RECIBO DE PAGO SEMANAL`;
                const metodoFinal = esExoneracion ? `N/A (EXONERADO)` : (d.metodo_pago || 'Efectivo');
                const detalleReferencia = esExoneracion ? `MOTIVO: ${novedadTexto}` : `REF. PAGO: ${referenciaManual}`;

                const contenidoRecibo = 
                `ASOC. COOP. LOS PATRIOTAS DE TÁRIBA R.L\n` +
                `CONTROL INTERNO: ${nroControlFinal}\n` + 
                `${tituloRecibo}\n` +
                `--------------------------------------------\n` +
                `UNIDAD: ${unidad}\n` +
                `CONDUCTOR: ${nombreConductor}\n` +
                `SEMANA FACTURADA: Semana Num. ${numeroSemanaRecibo}\n` + // 🎯 ¡AQUÍ SE REFLEJA!
                `ESTADO: ${esExoneracion ? 'EXONERADO' : 'PAGADO'}\n` +
                `VALOR CUOTA: COP ${montoReal}\n` + 
                `METODO: ${metodoFinal}\n` +
                `${detalleReferencia}\n` + 
                `FECHA: ${fecha}\n` +
                `--------------------------------------------\n` +
                `Comprobante generado por el sistema de gestión.`;

                // Descarga automática del archivo .txt para la ticketera
                const blob = new Blob([contenidoRecibo], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const prefijoArchivo = esExoneracion ? 'Exoneracion' : 'Recibo';
                a.download = `${prefijoArchivo}_Ctrl_${nroControlFinal}_Sem_${numeroSemanaRecibo}_Uni_${unidad}.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                alert(`✅ ${esExoneracion ? 'Exoneración registrada' : 'Pago registrado'} con Control Interno: ${nroControlFinal}`);

                // Reset completo del formulario y re-sincronización visual
                formElement.reset();
                if(selectNovedad) selectNovedad.dispatchEvent(new Event('change'));
                if(selectConductor) selectConductor.dispatchEvent(new Event('change')); // Fuerza el bloqueo del select de semanas
                
                if (window.cargarConductoresSelect) window.cargarConductoresSelect();
                if (window.cargarEstadoSemana) window.cargarEstadoSemana();

            } catch (err) {
                console.error("Error:", err);
                alert("Error al procesar el registro o generar el soporte.");
            }
            if (typeof cargarHistorialPagos === 'function') cargarHistorialPagos();
        });
    }  
  // ===================================================
    // 🚨 NUEVA ESCUCHA DE EVENTOS PARA EL MODAL DE INCIDENCIAS
    // ===================================================
    const textarea = document.getElementById("incid_descripcion");
    const select = document.getElementById("incid_categoria");

    if (textarea) {
        textarea.addEventListener("input", validarFormularioIncidencia);
    }

    if (select) {
        select.addEventListener("change", () => {
            actualizarOrigenReporte();
            validarFormularioIncidencia();
        });
    }
  //////////Reporte consolidado de pagos semanales por conductor (Modal de Contabilidad)
    document.getElementById('btnReporteConsolidado').addEventListener('click', async () => {
        const btn = document.getElementById('btnReporteConsolidado');
        const tabla = document.getElementById('tablaConsolidadoReporte');
        const tbody = document.getElementById('tbodyConsolidadoReporte');
        
        // Feedback visual de carga en el botón
        btn.innerHTML = '⏳ Generando...';
        btn.disabled = true;

        try {
            // Ejecutamos la petición usando su estructura de rutas
            const response = await apiFetch('/reportes/consolidado_pagos');
            
            if (response.status === 'success') {
                tbody.innerHTML = ''; // Limpiamos residuos viejos
                
                // 1. Renderizar los conductores uno a uno
                response.data.forEach(c => {
                    const fila = document.createElement('tr');
                    fila.className = 'hover:bg-gray-50 transition-colors';
                    fila.innerHTML = `
                        <td class="p-3 text-center font-semibold border-r bg-gray-50/50">${c.unidad}</td>
                        <td class="p-3 font-medium text-gray-800">${c.conductor}</td>
                        <td class="p-3 text-right font-semibold text-gray-700 border-l">$${c.total_pagado}</td>
                        <td class="p-3 text-center font-semibold text-blue-600 border-l">${c.semanas_cubiertas} sem</td>
                    `;
                    tbody.appendChild(fila);
                });

                // 2. Inyectar los Grandes Totales en el tfoot
                document.getElementById('totalConsolidadoDinero').innerText = `$${response.totales_generales.gran_total_dinero}`;
                document.getElementById('totalConsolidadoSemanas').innerText = `${response.totales_generales.gran_total_semanas} semanas`;

                // 3. Hacer visible la tabla quitándole el 'hidden' de Tailwind
                tabla.classList.remove('hidden');
            } else {
                alert('⚠️ Error al obtener el consolidado: ' + response.message);
            }
        } catch (error) {
            console.error('Error en reporte consolidado:', error);
            alert('❌ Error de conexión con el servidor de reportes.');
        } finally {
            // Restaurar estado del botón original
            btn.innerHTML = '🔄 Generar Consolidado Anual';
            btn.disabled = false;
        }
    });  
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
        //console.trace("DEBUG: ¿Quién llamó a abrirVista?:", idVista);
        const rolRaw = localStorage.getItem("rol");
        const rol = (rolRaw || "").trim().toLowerCase();
        
        // AGREGA ESTO PARA DEPURAR
        console.log("DEBUG: Rol detectado en localStorage:", rolRaw, "Procesado:", rol);
        
              
        // 1. Normalizar ID
        let idReal = (idVista === 'clientes' || idVista === 'clientesSection') ? 'clientesSection' : idVista;
        
        // 2. Control de seguridad
        if (idReal === 'clientesSection' && rol !== 'admin') {
            console.warn("⚠️ Acceso denegado: Vista de clientes requiere rol admin.");
            idReal = 'despachos'; 
        }

        // 3. OBTENER EL ELEMENTO REAL (Aquí estaba el fallo)
        const vista = document.getElementById(idReal);

        // 4. Lógica de activación
        if (vista) {
            // Ocultar todas las secciones antes de mostrar la seleccionada
            document.querySelectorAll('.seccion').forEach(s => s.classList.add('hidden'));
            
            vista.classList.remove("hidden");
            vista.style.display = 'block';
            
            if (window.vistaActual !== idReal) {
                console.log(`✅ Vista activa: ${idReal}`);
                window.vistaActual = idReal;
            }

            // Carga de datos condicional
            if (idReal === 'pagos') {
                if (window.cargarConductoresSelect) window.cargarConductoresSelect();
                if (window.cargarHistorialPagos) window.cargarHistorialPagos();
                if (window.cargarEstadoSemana) window.cargarEstadoSemana();
            }
        } else if (idReal !== 'despachos') {
            // Fallback si la vista no existe
            abrirVista('despachos');
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
        if (!select) return;

        try {
            console.log("📡 Probando ruta de solvencia...");
            
            // PRUEBA ESTA RUTA EXACTA (con el prefijo del blueprint)
            const data = await apiFetch('/pagos/estado_semana'); 
                      
            data.sort((a, b) => a.unidad.localeCompare(b.unidad, undefined, {numeric: true, sensitivity: 'base'}));
            if (Array.isArray(data)) {
                select.innerHTML = '<option value="">Seleccione Unidad / Conductor...</option>';
                data.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id_conductor;
                    // RECUERDE: En /estado_semana los campos son 'unidad' y 'conductor'
                    opt.textContent = `[Uni ${c.unidad}] - ${c.conductor}`;
                    select.appendChild(opt);
                });
                console.log(`✅ ${data.length} conductores cargados con éxito`);
            }
        } catch (err) {
            console.error("❌ Error 404 detectado. Intente cambiar la ruta en apiFetch", err);
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
                    ${(Number(p.monto) || 0).toLocaleString('es-VE')} COP
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
        let conductores = await apiFetch('/pagos/estado_semana');
        
        // 🎯 ORDENAMIENTO ALFANUMÉRICO DIRECTO EN EL FRONTEND
        if (conductores && conductores.length > 0) {
            conductores.sort((a, b) => {
                // Compara la propiedad 'unidad' (Ej: B1, B2, B10, B26) de forma natural humana
                return a.unidad.localeCompare(b.unidad, undefined, {
                    numeric: true,
                    sensitivity: 'base'
                });
            });
            console.log("📌 Tabla ordenada alfanuméricamente por código de unidad.");
        }

        // Limpiar tabla después de tener los datos listos y ordenados
        tbody.innerHTML = '';

        if (!conductores || conductores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-gray-500">No hay datos para esta semana.</td></tr>';
            return;
        }

        conductores.forEach(c => {
            const idValue = c.id_conductor; 
            const nombreValue = c.conductor;

            const fila = `
                <tr class="border-b hover:bg-gray-50">
                    <td class="p-2 text-center font-mono font-bold">${c.unidad}</td>
                    <td class="p-2 text-sm">${nombreValue}</td>
                    <td class="p-2 text-right font-mono font-bold">$${c.saldo}</td>
                    <td class="p-2 text-center">${c.status_html}</td>
                    <td class="p-2 font-semibold text-gray-700">${c.semanas_progreso || 'N/A'}</td>
                    <td class="p-2 text-center">
                        ${parseFloat(c.saldo) > 0 ? 
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

// 🚀 Variable de control de tiempo fuera de la función
let ultimoDisparoTiempo = 0;

window.prepararCobro = function(id, nombre) {
    const ahora = Date.now();
    
    // 1️⃣ DEBOUNCE: Control de ráfagas físicas de clics
    if (ahora - ultimoDisparoTiempo < 500) {
        console.warn("⚠️ Intento de ejecución duplicada frenado por seguridad de tiempo (Debounce).");
        return;
    }
    
    ultimoDisparoTiempo = ahora;
    console.log("🚀 PUENTE ACTIVADO REAL Y ÚNICO -> ID:", id, "Nombre:", nombre);

    window.conductorTieneSemana1 = false; // Inicialización por defecto

    // 🎯 CALCULO DINÁMICO DEL AÑO: Evitamos dejar "2026-01" fijo
    const anioActual = new Date().getFullYear(); 
    const semana1Dinamica = `${anioActual}-01`; // Genera "2026-01", "2027-01", etc.

    if (typeof window.matrizConductores !== 'undefined') {
        const conductorData = window.matrizConductores.find(c => String(c.id) === String(id));
        
        if (conductorData) {
            // Evaluamos la semana inicial de forma totalmente dinámica
            if (conductorData.semana_anio === semana1Dinamica) {
                window.conductorTieneSemana1 = true;
            } 
            
            console.log(`📊 Auditoría local: ¿${nombre} tiene la semana '${semana1Dinamica}'? ->`, window.conductorTieneSemana1);
        }
    }

    // CAPTURA DE NODOS DEL DOM
    const inputId = document.getElementById('modal_conductor_id');
    const elementoNombre = document.getElementById('modal_nombre_conductor');
    const inputMonto = document.getElementById('modal_monto'); 
    const selectExonerar = document.getElementById('modal_exonerar_sn');
    const selectIngreso = document.getElementById('modal_semana_ingreso');
    const inputReferencia = document.getElementById('modal_referencia');

    // 2️⃣ RESETEAR ESTADOS POR DEFECTO DEL FORMULARIO
    if (selectExonerar) selectExonerar.value = ""; 
    if (selectIngreso) selectIngreso.value = "1";
    if (inputMonto) {
        inputMonto.value = ""; 
        inputMonto.disabled = false; // Aseguramos que empiece liberado
        inputMonto.classList.remove('bg-gray-100', 'cursor-not-allowed');
    }
    if (inputReferencia) {
        inputReferencia.value = "";
        inputReferencia.placeholder = `Ej: NIVELACIÓN INICIAL ${anioActual}`;
    }

    // INYECCIÓN DE DATOS DEL CONDUCTOR
    if (inputId) inputId.value = id;
    if (elementoNombre) {
        if (elementoNombre.tagName === 'INPUT') {
            elementoNombre.value = nombre;
        } else {
            elementoNombre.innerText = nombre;
        }
    }

    // =========================================================================
    // 🎛️ ESCUCHADOR INTERACTIVO (EVITAR QUE ESCRIBAN MONTO SI EXONERAN)
    // =========================================================================
    if (selectExonerar && inputMonto) {
        // Removemos cualquier listener viejo clonando el nodo (evita acumular eventos si reabren el modal)
        const nuevoSelect = selectExonerar.cloneNode(true);
        selectExonerar.parentNode.replaceChild(nuevoSelect, selectExonerar);

        nuevoSelect.addEventListener('change', function() {
            if (this.value === 'SI') {
                // 🔒 Bloqueo inmediato: Es una gracia, no maneja dinero en caja
                inputMonto.value = '0';
                inputMonto.disabled = true;
                inputMonto.classList.add('bg-gray-100', 'cursor-not-allowed');
                if (inputReferencia) inputReferencia.placeholder = "Ej: EXONERACIÓN POR REINGRESO / TALLER";
            } else {
                // 🔓 Liberación: Es un cobro o abono normal
                inputMonto.value = '';
                inputMonto.disabled = false;
                inputMonto.classList.remove('bg-gray-100', 'cursor-not-allowed');
                if (inputReferencia) inputReferencia.placeholder = `Ej: NIVELACIÓN INICIAL ${anioActual}`;
            }
        });
    }
   
    // APERTURA DEL MODAL
    const modal = document.getElementById('modalCargaInicial');
    if (modal) {
        modal.classList.remove('hidden');
    } else {
        console.error("❌ Error fatal: No se encontró el modal 'modalCargaInicial'");
    }
};
// El resto de sus funciones (cerrarModalCarga y onsubmit) se mantienen igual abajo...


let idDespachoGlobal = null;
let idClienteGlobal = null;
let idConductorGlobal = null;

function abrirModalIncidenciaSeguro(datosCodificados) {
    try {
        // Decodificar el objeto completo del despacho
        const despacho = JSON.parse(decodeURIComponent(datosCodificados));
        console.log("📥 [MODAL] Objeto completo recibido de la tabla:", despacho);

        // 1. Extraer ID del Despacho
        idDespachoGlobal = despacho.id_despacho || despacho.id || null;

        // 2. Extraer ID del Cliente probando todos los nombres de campo existentes
        idClienteGlobal = despacho.cliente_id || despacho.id_cliente || despacho.id_cliente_fk || despacho.cliente || null;

        // 3. Extraer ID del Conductor probando todas las variantes
        idConductorGlobal = despacho.conductor_id || despacho.id_conductor || despacho.id_conductor_fk || despacho.conductor || null;

        console.log("📌 [MODAL] IDs guardados en memoria:", { idDespachoGlobal, idClienteGlobal, idConductorGlobal });

        const modal = document.getElementById("modalIncidencia");
        if (!modal) return;

        modal.classList.remove("hidden");

        // Pintar en la interfaz del modal para confirmar visualmente
        if (document.getElementById("lblIncidCliente")) {
            document.getElementById("lblIncidCliente").textContent = idClienteGlobal || "N/D";
        }
        if (document.getElementById("lblIncidConductor")) {
            document.getElementById("lblIncidConductor").textContent = idConductorGlobal || "N/D";
        }

        // Limpiar campos de entrada
        if (document.getElementById("incid_categoria")) document.getElementById("incid_categoria").value = "";
        if (document.getElementById("incid_descripcion")) document.getElementById("incid_descripcion").value = "";

    } catch (error) {
        console.error("❌ Error al procesar los datos del despacho:", error);
    }
}

// Hacerla accesible globalmente en el navegador
window.abrirModalIncidencia = abrirModalIncidenciaSeguro;

async function guardarIncidencia(event) {
    if (event) event.preventDefault();

    const payload = {
        despacho_id: idDespachoGlobal ? parseInt(idDespachoGlobal) : null,
        cliente_id: idClienteGlobal ? parseInt(idClienteGlobal) : null,
        conductor_id: idConductorGlobal ? parseInt(idConductorGlobal) : null,
        categoria: document.getElementById('incid_categoria').value,
        origen_reporte: document.getElementById('incid_origen_reporte')?.value || "CONDUCTOR",
        descripcion: document.getElementById('incid_descripcion').value.trim()
    };

    console.log("📤 [API] Objeto que se enviará al servidor:", payload);

    if (!payload.despacho_id || !payload.cliente_id || payload.cliente_id === 0) {
        alert("⚠️ Error local: No se ha capturado el ID del cliente o del despacho.");
        return;
    }

    try {
        const data = await apiFetch('/incidencias/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        if (data && (data.success || data.id_incidencia || data.msg)) {
            alert("✅ Incidencia guardada con éxito");
            cerrarModalIncidencia();
            if (document.getElementById('formIncidencia')) {
                document.getElementById('formIncidencia').reset();
            }
            idDespachoGlobal = null;
            idClienteGlobal = null;
            idConductorGlobal = null;
        } else {
            alert("❌ Error: " + (data?.error || "Intente nuevamente"));
        }
    } catch (error) {
        console.error("❌ Error en la solicitud de guardado:", error);
    }
}

// Hacerlas accesibles en el scope global
window.guardarIncidencia = guardarIncidencia;

function cerrarModalIncidencia() {
    document.getElementById('modalIncidencia').classList.add('hidden');
}

// ===================================================
// 1. DETECTAR EL ORIGEN DEL REPORTE SEGÚN EL OPTGROUP
// ===================================================
function actualizarOrigenReporte() {
    const selectCategoria = document.getElementById("incid_categoria");
    if (!selectCategoria) {
        console.error("❌ No se encontró el elemento #incid_categoria");
        return;
    }

    const optionSeleccionada = selectCategoria.options[selectCategoria.selectedIndex];
    if (!optionSeleccionada || !optionSeleccionada.parentNode) return;

    const optgroup = optionSeleccionada.parentNode.label; 
    const inputOrigen = document.getElementById("incid_origen_reporte");

    if (inputOrigen) {
        if (optgroup === "Reportado por el Conductor (Hacia el Cliente)") {
            inputOrigen.value = "CONDUCTOR";
        } else if (optgroup === "Reportado por el Cliente (Hacia el Conductor)" || optgroup === "Casos Administrativos") {
            inputOrigen.value = "CLIENTE";
        }
        console.log("🎯 Origen asignado:", inputOrigen.value);
    }
    
    // Forzamos la validación del formulario inmediatamente
    validarFormularioIncidencia();
}

function validarFormularioIncidencia() {
    const select = document.getElementById("incid_categoria");
    const textarea = document.getElementById("incid_descripcion");
    const btnGuardar = document.getElementById("btnGuardarIncidencia");

    // Imprimimos en consola para ver qué está encontrando el script
    console.log("🔍 Estado de los elementos en el DOM:", {
        select: select ? "Encontrado" : "No encontrado",
        textarea: textarea ? "Encontrado" : "No encontrado",
        boton: btnGuardar ? "Encontrado" : "No encontrado"
    });

    if (!select || !textarea || !btnGuardar) return;

    const categoria = select.value;
    const descripcion = textarea.value.trim();

    console.log(`📝 Validando datos -> Categoría: "${categoria}", Descripción: "${descripcion}" (Largo: ${descripcion.length})`);

    // Condición para activar: Categoría seleccionada y al menos 5 caracteres en la descripción
    if (categoria !== "" && descripcion.length >= 5) {
        console.log("🔓 ACTIVANDO BOTÓN");
        btnGuardar.disabled = false;
        btnGuardar.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
        console.log("🔒 BLOQUEANDO BOTÓN");
        btnGuardar.disabled = true;
        btnGuardar.classList.add("opacity-50", "cursor-not-allowed");
    }
}

// Las hacemos globales para que el HTML y la consola puedan llamarlas
window.actualizarOrigenReporte = actualizarOrigenReporte;
window.validarFormularioIncidencia = validarFormularioIncidencia;
// =================================================================
// CALCULADORA EXPRESS: CONVERSIÓN DE COP A VES PARA OPERADORAS
// =================================================================

function inicializarCalculadoraCopToVes() {
    const modalCalc = document.getElementById('modalCalculadoraBs');
    if (!modalCalc) return;

    const inputTasa = document.getElementById('calc_tasa');
    const inputCop = document.getElementById('calc_monto_cop');
    const inputBs = document.getElementById('calc_resultado_bs');
    const btnCopiar = document.getElementById('btn_copiar_bs');

    // Recuperamos la última tasa guardada del localStorage
    const tasaGuardada = localStorage.getItem('tasa_dia_cop');
    if (tasaGuardada && inputTasa) {
        inputTasa.value = tasaGuardada;
    }

    // Función que realiza el cálculo matemático
    const calcular = () => {
        const tasa = parseFloat(inputTasa.value) || 0;
        const pesos = parseFloat(inputCop.value) || 0;

        // Guardamos la tasa actual para la próxima vez
        localStorage.setItem('tasa_dia_cop', inputTasa.value);

        if (tasa > 0 && pesos > 0) {
            // Dividimos Pesos entre la tasa para obtener Bolívares
            const bolivares = pesos / tasa;
            
            // Mostramos el resultado formateado con 2 decimales
            inputBs.value = bolivares.toLocaleString('es-VE', { 
                minimumFractionDigits: 2, 
                maximumFractionDigits: 2 
            });
        } else {
            inputBs.value = '0,00';
        }
    };

    // 🚀 EVENTO CLAVE: Escucha cuando la operadora escribe o borra en tiempo real
    if (inputCop) {
        inputCop.addEventListener('input', calcular);
    }
    if (inputTasa) {
        inputTasa.addEventListener('input', calcular);
    }

    // Configuración al abrir el modal
    modalCalc.addEventListener('shown.bs.modal', () => {
        if (inputCop) {
            inputCop.value = '';
            inputCop.focus(); // Coloca el cursor directamente en el campo de pesos
        }
        if (inputBs) {
            inputBs.value = '0,00';
        }
    });

    // Acción del botón copiar
    if (btnCopiar) {
        btnCopiar.addEventListener('click', () => {
            const valorLimpio = inputBs.value.replace(/\./g, '').replace(',', '.');
            if (valorLimpio !== '0.00') {
                navigator.clipboard.writeText(valorLimpio);
                
                const originalText = btnCopiar.innerText;
                btnCopiar.innerText = '✅';
                setTimeout(() => { btnCopiar.innerText = originalText; }, 1000);
            }
        });
    }
}

// Ejecutamos la función directamente
inicializarCalculadoraCopToVes();
function restringirAccesoPorRol() {
    const rolNombre = localStorage.getItem("rol_nombre");
    const rolSimple = localStorage.getItem("rol");
    const rolFinal = rolNombre || rolSimple;

    console.log("🔍 Intento de lectura de rol:", rolFinal);

    const contenedorContabilidad = document.querySelector(".mt-8.border-t.pt-6");
    const btnReportePagos = document.getElementById("btnReportePagos");
    const btnImprimir = document.getElementById("btnImprimirCierre"); // 👈 AGREGADO

    if (!rolFinal) {
        console.warn("⚠️ Rol no encontrado, reintentando en 500ms...");
        setTimeout(restringirAccesoPorRol, 500);
        return;
    }

    const rolLower = rolFinal.toLowerCase().trim();

    if (rolLower === "administrador" || rolLower === "admin") {
        console.log("✅ Acceso administrativo confirmado para:", rolFinal);
    
        if (contenedorContabilidad) {
            contenedorContabilidad.style.display = "block";
            if (btnReportePagos) btnReportePagos.style.display = "inline-block";

            // 🚨 OPERACIÓN RESCATE PDF
            let btnImprimir = document.getElementById("btnImprimirCierre");
            
            if (!btnImprimir) {
                console.warn("⚠️ Botón PDF no existe en el HTML. Creándolo dinámicamente...");
                // Si el botón no existe, lo inyectamos al lado del amarillo
                const nuevoBtn = document.createElement('button');
                nuevoBtn.id = "btnImprimirCierre";
                nuevoBtn.innerHTML = '<i class="fas fa-file-pdf"></i> Imprimir PDF';
                nuevoBtn.className = "bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded flex items-center gap-2 ml-2";
                nuevoBtn.style.display = "inline-flex";
                
                // Lo insertamos justo después del botón amarillo
                btnReportePagos.parentNode.insertBefore(nuevoBtn, btnReportePagos.nextSibling);
                nuevoBtn.onclick = function() {
                    const inicio = document.getElementById('fechaInicioContable').value;
                    const fin = document.getElementById('fechaFinContable').value;

                    if (!inicio || !fin) {
                        alert("Por favor seleccione el rango de fechas primero.");
                        return;
                    }

                    const token = localStorage.getItem('access_token');
                    const url = `/reportes/pdf_pagos?inicio=${inicio}&fin=${fin}`;

                    fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
                        .then(response => response.blob())
                        .then(blob => {
                            const urlBlob = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = urlBlob;
                            a.download = `Cierre_Caja_${inicio}.pdf`;
                            a.click();
                        })
                        .catch(err => console.error("Error:", err));
                };
                // ... dentro de la creación dinámica del botón ...
                nuevoBtn.onclick = function() {
                    // Intentamos capturar los IDs que usa el botón amarillo
                    // Si el amarillo funciona, use exactamente los mismos IDs aquí
                    const campoInicio = document.getElementById('fechaInicio') || document.getElementById('fechaInicioContable');
                    const campoFin = document.getElementById('fechaFin') || document.getElementById('fechaFinContable');

                    if (!campoInicio || !campoFin) {
                        console.error("❌ No se encontraron los inputs de fecha en el DOM");
                        alert("Error técnico: No se encuentran los campos de fecha.");
                        return;
                    }

                    const inicio = campoInicio.value;
                    const fin = campoFin.value;

                    if (!inicio || !fin) {
                        alert("Por favor seleccione el rango de fechas primero.");
                        return;
                    }

                    console.log("🚀 Enviando a imprimir pagos desde:", inicio, "hasta:", fin);
                    
                    const token = localStorage.getItem('access_token');
                    const url = `/reportes/pdf_pagos?inicio=${inicio}&fin=${fin}`;

                    fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
                        .then(response => {
                            if (!response.ok) throw new Error("Fallo en la respuesta del servidor");
                            return response.blob();
                        })
                        .then(blob => {
                            const urlBlob = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = urlBlob;
                            a.download = `Cierre_Caja_${inicio}.pdf`;
                            document.body.appendChild(a); // Agregamos al body por seguridad
                            a.click();
                            a.remove();
                        })
                        .catch(err => alert("Error al descargar PDF: " + err.message));
                };
            } else {
                // Si existe, forzamos su visibilidad total
                btnImprimir.style.setProperty('display', 'inline-flex', 'important');
                btnImprimir.style.setProperty('visibility', 'visible', 'important');
                btnImprimir.classList.remove('hidden');
                console.log("📕 Botón PDF forzado a visible.");
            }
        }
    } else {
        console.log("🚫 Rol operativo detectado. Ocultando contabilidad.");
        if (btnReportePagos) btnReportePagos.style.display = "none";
        if (btnImprimir) btnImprimir.style.display = "none"; // 👈 OCULTAR TAMBIÉN
        if (contenedorContabilidad) contenedorContabilidad.style.display = "none";
    }
}
// 1. Defina la función en cualquier parte de su dashboard.js
window.inicializarBotonImpresion = function() {
    const btnImprimir = document.getElementById('btnImprimirCierre');
    if (btnImprimir) {
        // Limpiamos el botón
        const btnLimpio = btnImprimir.cloneNode(true);
        btnImprimir.parentNode.replaceChild(btnLimpio, btnImprimir);

        btnLimpio.addEventListener('click', function() {
            const campoInicio = document.getElementById('fechaInicio') || document.getElementById('fechaInicioContable');
            const campoFin = document.getElementById('fechaFin') || document.getElementById('fechaFinContable');

            if (!campoInicio?.value || !campoFin?.value) {
                alert("Por favor seleccione el rango de fechas.");
                return;
            }

            // 🎯 Capturamos el token real que sabemos que se llama 'token'
            const token = localStorage.getItem('token'); 
            
            const url = `/reportes/generar_cierre_pdf?inicio=${campoInicio.value}&fin=${campoFin.value}&token=${token}`;
            
            console.log("🚀 Disparando descarga directa...");
            // Abrimos en pestaña nueva para que el navegador gestione la descarga
            window.open(url, '_blank'); 
        });
    }
};
// 🕵️ El Vigilante Global (Delegación de eventos)
document.addEventListener('click', function (event) {
    // Si el elemento clicado es nuestro botón de reporte
    if (event.target && event.target.id === 'btnReporteEmbarque') {
        console.log("🎯 Clic detectado por el Vigilante Global");
        window.forzarReporte();
    }
});

// Su función se queda igual, pero asegúrese de que esté así:
window.forzarReporte = async function() {
    console.log("🚀 Disparo manual iniciado...");
    
    // 1. Buscamos el contenedor padre primero
    const seccionReportes = document.getElementById("reportes"); 
    if (!seccionReportes) {
        console.error("❌ No se encontró la sección de reportes.");
        return;
    }

    const inicio = seccionReportes.querySelector("#fechaInicio")?.value;
    const fin = seccionReportes.querySelector("#fechaFin")?.value;

    if (!inicio || !fin) {
        alert("Ingeniero, seleccione las fechas en la sección activa.");
        return;
    }

    // 2. Buscamos la tabla SOLO dentro de esta sección
    const tabla = seccionReportes.querySelector("#tabla-reporte");
    
    if (tabla) {
        console.log("✅ Tabla encontrada en la sección activa. Cargando...");
        await cargarReporteEmbarqueDesembarque(inicio, fin, tabla);
    } else {
        console.error("❌ La tabla no existe dentro de la sección de reportes.");
        // Si no existe, la creamos a la fuerza
        const contenedorTabla = seccionReportes.querySelector("#reporte-container");
        if (contenedorTabla) {
            contenedorTabla.innerHTML = `
                <table class="w-full mt-2 border">
                    <thead>
                        <tr><th>Nro</th><th>Cliente</th><th>Teléfono</th><th>Conductor</th><th>Embarque</th><th>Desembarque</th></tr>
                    </thead>
                    <tbody id="tabla-reporte"></tbody>
                </table>`;
            const nuevaTabla = seccionReportes.querySelector("#tabla-reporte");
            await cargarReporteEmbarqueDesembarque(inicio, fin, nuevaTabla);
        }
    }
};

// =========================================================================
// 🧼 1. FUNCIÓN LEGÍTIMA DE CIERRE UNIFICADA Y BLINDADA (EVITA DUPLICIDAD)
// =========================================================================
window.cerrarModalCarga = function() {
    const modal = document.getElementById('modalCargaInicial');
    const form = document.getElementById('formCargaInicial');
    
    if (modal) modal.classList.add('hidden');
    
    if (form) {
        form.reset();
        
        const elMonto = document.getElementById('modal_monto');
        const elSemana = document.getElementById('modal_semana_ingreso');
        const contenedorSemana = document.getElementById('contenedor_semana_ingreso');
        
        // Retornamos todo a estado Neutro Seguro de fábrica
        if (contenedorSemana) contenedorSemana.classList.add('hidden');
        if (elSemana) {
            elSemana.disabled = true;
            elSemana.innerHTML = '';
        }
        if (elMonto) {
            elMonto.value = '';
            elMonto.disabled = true;
            elMonto.classList.add('bg-gray-100', 'cursor-not-allowed');
        }
    }
};

// 2. Bandera única de control de concurrencia en memoria
// 🚨 ASEGURAMOS LA INICIALIZACIÓN GLOBAL FUERA DE LA FUNCIÓN
if (typeof window.peticionEnCurso === 'undefined') {
    window.peticionEnCurso = false;
}
// =========================================================================
// 🔄 DELEGACIÓN DE EVENTOS GLOBAL (INMUNE A CAMBIOS DE VISTA Y ASINCRONISMO)
// =========================================================================
document.addEventListener('change', async function(event) {
    if (event.target && event.target.id === 'modal_exonerar_sn') {
        
        console.log("🎯 [DELEGACIÓN] Cambio detectado en 'modal_exonerar_sn' de forma dinámica.");
        
        const elSelect = event.target;
        const elMonto = document.getElementById('modal_monto');
        const elRef = document.getElementById('modal_referencia');
        const elSemana = document.getElementById('modal_semana_ingreso');
        const contenedorSemana = document.getElementById('contenedor_semana_ingreso');
        const conductorId = document.getElementById('modal_conductor_id') ? document.getElementById('modal_conductor_id').value : '';
        
        // 🧼 Estado de Limpieza Inmediata antes de evaluar escenarios
        if (contenedorSemana) contenedorSemana.classList.add('hidden');
        if (elSemana) { elSemana.disabled = true; elSemana.innerHTML = ''; }
        if (elMonto) {
            elMonto.value = "0";
            elMonto.disabled = true;
            elMonto.classList.add('bg-gray-100', 'cursor-not-allowed');
        }

        // ❌ ESCENARIO "NO": Cargar Deuda Completa (Carga Masiva Estándar)
        if (elSelect.value === 'NO') {
            console.log("💼 Activando Modo: Carga Masiva Estándar.");
            if (elMonto) {
                elMonto.value = ""; // Se limpia el cero para que digite el monto real
                elMonto.disabled = false;
                elMonto.classList.remove('bg-gray-100', 'cursor-not-allowed');
                elMonto.focus();
            }
            if (elRef) {
                elRef.placeholder = "Ej: NIVELACIÓN INICIAL 2026";
            }
        } 
        
        // ✅ ESCENARIO "SI": Ingreso Tardío (Exonerar semanas anteriores)
        else if (elSelect.value === 'SI') {
            console.log("⏳ Activando Modo: Validación de Ingreso Tardío.");
            
            if (elSemana) {
                elSemana.disabled = true; 
                elSemana.innerHTML = '<option value="">⏳ Validando antecedentes en base de datos...</option>';
                if (contenedorSemana) contenedorSemana.classList.remove('hidden');
                
                if (!conductorId) {
                    alert("❌ Error: Conductor no identificado.");
                    elSelect.value = "";
                    if (contenedorSemana) contenedorSemana.classList.add('hidden');
                    return;
                }

                try {
                    // 📡 ALCABALA DE SEGURIDAD: Consultamos las semanas en base de datos
                    const response = await fetch(`/pagos/semanas_pendientes/${conductorId}`, {
                        method: 'GET',
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                    });

                    if (response.ok) {
                        const datos = await response.json();
                        // 💡 Ajustamos la lectura: Dependiendo de cómo responda su endpoint, 
                        // si devuelve un objeto con la propiedad semanas o directamente el Array.
                        const listaSemanas = (datos && datos.semanas && Array.isArray(datos.semanas)) 
                            ? datos.semanas 
                            : (Array.isArray(datos) ? datos : []);

                        // 📅 Detectamos las etiquetas del año actual
                        const anioActual = new Date().getFullYear();
                        const semanaUnoLabel = `${anioActual}-01`;

                        // 🎯 REGLA DEL INGENIERO EN JS: 
                        // Buscamos si en la lista de semanas ya existe la semana 1 modificada, o si el backend 
                        // reporta que ya no está pendiente porque ya fue procesada previamente.
                        
                        // Evalúa si la semana 1 ya no figura como pendiente limpia, o si viene marcada.
                        // (Flexibilizamos a doble igual == para cubrir si viene como 1, "1" o true)
                        const tieneHistorialSemanaUno = listaSemanas.some(reg => {
                            if (reg.semana_anio === semanaUnoLabel) {
                                // Si la semana 1 existe en la lista pero ya está marcada como pagada o exonerada
                                return reg.pagado == true || reg.pagado == 1 || reg.es_exonerado == 1 || reg.es_exonerado == "SI";
                            }
                            return false;
                        });

                        // 🚨 SEGUNDO SEGURO CONTABLE: Si el endpoint de pendientes NO devuelve la semana 1, 
                        // significa que Flask ya la procesó, la saldó y la sacó de la lista de mora.
                        const semanaUnoAusente = !listaSemanas.some(reg => reg.semana_anio === semanaUnoLabel);

                        // Si tiene historial asentado o ya se consolidó (ausente en deudas), se corta el flujo
                        if (tieneHistorialSemanaUno || (listaSemanas.length > 0 && semanaUnoAusente)) {
                            
                            alert(`🚫 Operación denegada:\n\nEl conductor ya posee un historial contable activo o cargas masivas previas en el sistema.\n\nNo es posible aplicar una exoneración masiva por Ingreso Tardío si ya cuenta con registros en la Semana 01.`);
                            
                            elSelect.value = ""; 
                            if (contenedorSemana) contenedorSemana.classList.add('hidden');
                            elSemana.innerHTML = '';
                            return; 
                        }

                        // 🔓 CASO SEGURO (Ender Fulá y conductores limpios): Reconstruimos el select
                        elSemana.innerHTML = ''; 

                        // 📅 Cálculo dinámico de semanas del año (2026)
                        const hoy = new Date();
                        const inicioAño = new Date(hoy.getFullYear(), 0, 1);
                        const diasPasados = Math.floor((hoy - inicioAño) / (24 * 60 * 60 * 1000));
                        const semanaActualDelAño = Math.ceil((diasPasados + inicioAño.getDay() + 1) / 7);

                        console.log(`🆕 Conductor apto verificado. Desplegando semanas desde la 02 hasta la ${semanaActualDelAño}`);

                        // Inyectamos opción neutra obligatoria
                        const optDefault = document.createElement('option');
                        optDefault.value = "";
                        optDefault.innerText = "-- Seleccione Semana de Ingreso Real --";
                        optDefault.disabled = true;
                        optDefault.selected = true;
                        elSemana.appendChild(optDefault);

                        // 📌 RELLENADO DE SEMANAS DESDE LA NRO 2 (Ingreso Tardío Estricto) hasta la actual
                        for (let i = 2; i <= semanaActualDelAño; i++) {
                            const option = document.createElement('option');
                            option.value = i;
                            option.innerText = `Ingresó en la Semana ${String(i).padStart(2, '0')}`;
                            elSemana.appendChild(option);
                        }
                        
                        elSemana.disabled = false; // Se libera para la interacción de la administradora

                    } else {
                        throw new Error("Fallo en la respuesta del servidor");
                    }
                } catch (error) {
                    console.error("❌ Error en alcabala contable:", error);
                    alert("⚠️ No se pudo verificar el historial debido a un problema de conexión.");
                    elSelect.value = "";
                    if (contenedorSemana) contenedorSemana.classList.add('hidden');
                }
            }

            if (elRef) {
                elRef.placeholder = "Ej: EXONERACIÓN POR INGRESO TARDÍO";
            }
        }
    }
});
// =========================================================================
// 🚀 PROCESAMIENTO GENERAL DE LA CARGA (CON ADUANAS CLÍNICAS)
// =========================================================================
window.ejecutarCargaInicial = async function(e) {
    if (e && typeof e.preventDefault === 'function') {
        e.preventDefault();
        e.stopPropagation();
    }

    if (window.peticionEnCurso) {
        console.warn("⛔ [SEMÁFORO] Bloqueado: Ya existe un envío contable en proceso.");
        return; 
    }

    const elExonerar = document.getElementById('modal_exonerar_sn');
    const elSemana = document.getElementById('modal_semana_ingreso');
    const elMonto = document.getElementById('modal_monto');
    const elRef = document.getElementById('modal_referencia');

    const aplicaExoneracion = elExonerar ? elExonerar.value : '';
    const montoRaw = elMonto ? elMonto.value : '';
    const referenciaInput = elRef ? elRef.value : '';

    if (!aplicaExoneracion) {
        alert("⚠️ Operación abortada: Debe seleccionar si aplica o no la Exoneración.");
        return;
    }

    // 🚨 VALIDACIÓN ESPECÍFICA PARA ESCENARIO "SÍ" (Ingreso Tardío)
    if (aplicaExoneracion === "SI" && (!elSemana || !elSemana.value)) {
        alert("⚠️ Operación abortada: Debe seleccionar la semana real en la que ingresó el conductor.");
        return;
    }

    let montoFinal = montoRaw === "" ? 0 : parseFloat(montoRaw);
    const TARIFA_SEMANAL = window.TARIFA_SEMANAL_SISTEMA || 40000;

    // VALIDACIONES DEL ESCENARIO "NO"
    if (aplicaExoneracion === "NO") {
        if (isNaN(montoFinal) || montoFinal <= 0) {
            alert("❌ Error: En el escenario de Carga Completa debe ingresar un monto válido en efectivo.");
            return;
        }
        if (montoFinal % TARIFA_SEMANAL !== 0) {
            alert(`❌ Monto Inválido: El valor ingresado debe ser un múltiplo exacto de ${TARIFA_SEMANAL.toLocaleString()} COP.`);
            return;
        }
        if (montoFinal === TARIFA_SEMANAL) {
            alert(`⚠️ Operación Rechazada: Para registrar una sola cuota (${TARIFA_SEMANAL.toLocaleString()} COP), use el módulo de taquilla ordinaria.`);
            return;
        }
    }

    const btn = document.getElementById('btnEnviarCarga');
    
    // 🧠 ASIGNACIÓN INTELIGENTE DE SEMANA SEGÚN ESCENARIO
    const valorSemana = aplicaExoneracion === "NO" ? 1 : parseInt(elSemana.value);

    const payloadFinal = {
        conductor_id: document.getElementById('modal_conductor_id').value,
        monto: montoFinal,
        referencia_pago: referenciaInput.trim() || (aplicaExoneracion === "SI" ? `EXONERACIÓN DESDE SEM ${valorSemana}` : "NIVELACIÓN INICIAL DEUDA"),
        semana_inicio: valorSemana,
        es_exonerado: aplicaExoneracion 
    };

    try {
        window.peticionEnCurso = true; 
        if (btn) {
            btn.disabled = true;
            btn.innerText = "Procesando...";
        }

        console.log("🎯 PAYLOAD VERIFICADO DESTINO FLASK:", payloadFinal);

        const response = await fetch('/pagos/carga_inicial_pagos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(payloadFinal)
        });

        if (response.ok) {
            alert('✅ Operación contable registrada con éxito.');
            window.cerrarModalCarga();
            if (typeof window.cargarEstadoSemana === 'function') await window.cargarEstadoSemana();
        } else {
            const err = await response.json();
            alert('❌ Error del Servidor: ' + (err.error || 'No se pudo procesar la carga inicial.'));
        }

    } catch (error) {
        console.error('❌ Error fatal en procesamiento:', error);
        alert('Error de conexión con el servidor');
    } finally {
        window.peticionEnCurso = false; 
        if (btn) {
            btn.disabled = false;
            btn.innerText = "PROCESAR TODO";
        }
    }
};
//////Botón reporte consolidado/////
document.getElementById('btnImprimirConsolidadoPDF').addEventListener('click', function() {
    const btn = this;
    const textoOriginal = btn.innerHTML;
    
    btn.innerHTML = '⏳ Generando PDF...';
    btn.disabled = true;

    // Abrimos directamente el endpoint en una ventana/pestaña oculta para disparar la descarga nativa
    window.location.href = '/reportes/pdf_consolidado';

    // Restauramos el botón después de un pequeño delay técnico
    setTimeout(() => {
        btn.innerHTML = textoOriginal;
        btn.disabled = false;
    }, 2000);
});

function abrirMonitoreo() {
    // Definimos el tamaño y características de la ventana
    const ancho = 1200;
    const alto = 800;
    const izquierda = (screen.width - ancho) / 2;
    const superior = (screen.height - alto) / 2;
    
    // Abrimos la ventana
    const ventanaMonitoreo = window.open(
        '/monitoreo', 
        'MonitoreoFlota', 
        `width=${ancho},height=${alto},left=${izquierda},top=${superior},toolbar=no,menubar=no,scrollbars=yes,resizable=yes`
    );

    // Opcional: Esto trae la ventana al frente si el operador ya la tenía abierta pero escondida
    if (ventanaMonitoreo) {
        ventanaMonitoreo.focus();
    }
}
function refrescarTodo() {
    console.log("🔄 Ejecutando refresco global...");
    
    // Aquí agrupas TODO lo que necesita actualizarse
    cargarTurnos();
    cargarConductores();        // Agregada de tu antiguo setTimeout
    cargarAutosTabla();         // Agregada de tu antiguo setTimeout
    
    if (typeof cargarConductoresEnTurnoCrear === 'function') {
        cargarConductoresEnTurnoCrear();
    }
    
    if (typeof cargarAutosDisponiblesSelect === 'function') {
        cargarAutosDisponiblesSelect();
    }
}
// --- ESCUCHA PROFESIONAL DE TELEGRAM ---
// Si ya tienes 'const socket = io();' arriba en el archivo, no lo dupliques.
// Si no lo tienes, asegúrate de añadirlo al inicio del archivo.

// 🛡️ Aseguramos que usamos la instancia global que definimos en el HTML
(function() {
    const socket = window.socket; // Referencia al socket global

    if (socket) {
        socket.on('turno_finalizado', (data) => {
            console.log("🔔 Aviso desde Telegram: Turno finalizado por", data.conductor);
            refrescarTodo(); 
        });
    } else {
        console.error("⚠️ El socket no está inicializado, verifica el orden de carga.");
    }
})();