// ===============================
// modales_tipo_despacho.js
// Lógica exclusiva para modal de Reserva (Corregido)
// ===============================

document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOMContentLoaded disparado (modales_tipo_despacho.js)");
  console.log("📍 Ejecutando lógica de reservas");
  verificarReservasAlCargar();

  const tipor = document.getElementById("tipoDespacho");
  const modalReservaEl = document.getElementById("modalDespachoReserva");

  // ---------------------------------------------------------
  // 1. GESTIÓN DE INSTANCIAS DEL MODAL
  // ---------------------------------------------------------
  if (modalReservaEl) {
    const existingInstance = bootstrap.Modal.getInstance(modalReservaEl);
    if (existingInstance) {
      existingInstance.dispose();
      console.log("♻️ Instancia previa de modalReserva descartada para liberar memoria");
    }

    window.modalReservaInstance = new bootstrap.Modal(modalReservaEl);
    console.log("✅ Instancia modalReserva creada");

    // Limpiar select y formulario al cerrar
    modalReservaEl.addEventListener("hidden.bs.modal", () => {
      console.log("🔄 Modal reserva cerrado, reiniciando select…");
      if (tipor) tipor.value = "";
      const form = modalReservaEl.querySelector("form");
      if (form) form.reset();
      
      const resCliente = document.getElementById("resCliente");
      const resOrigen = document.getElementById("resOrigen");
      if (resCliente) resCliente.removeAttribute("readonly");
      if (resOrigen) resOrigen.removeAttribute("readonly");
    });
  } 

  // ---------------------------------------------------------
  // 2. ATAJO DE TECLADO (Ctrl + R)
  // ---------------------------------------------------------
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key.toLowerCase() === "r") {
      event.preventDefault(); 

      const modalReservas = document.getElementById("modalListaReservas");
      if (modalReservas) {
        const modalInstance = new bootstrap.Modal(modalReservas);
        modalInstance.show();

        // ✅ Corregido al nombre real de la función
        cargarReservasPorVencer();
      }
    }
  });
  
  // ---------------------------------------------------------
  // 3. SELECT tipoDespacho → ABRIR MODAL
  // ---------------------------------------------------------
  if (tipor) {
    tipor.addEventListener("change", () => {
      const val = tipor.value;
      if (val === "reserva") {
        if (window.modalReservaInstance) window.modalReservaInstance.show();
      }
    });
  }

  // ---------------------------------------------------------
  // 4. LISTENER DE TELÉFONO (ENTER)
  // ---------------------------------------------------------
  const telefonoInput = document.getElementById("resTelefono");
  if (telefonoInput) {
    telefonoInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault(); 
        
        const telefono = telefonoInput.value.trim();
        if (telefono === "") return;

        const regexTelefono = /^(0276[0-9]{7}|04[0-9]{9})$/;
        if (!regexTelefono.test(telefono)) {
          mostrarToast("⚠️ Número de teléfono inválido.", "error");
          return;
        }

        try {
          const dataCliente = await apiFetch(`/clientes/telefono/${telefono}`);

          if (dataCliente && dataCliente.existe) {
            document.getElementById("resCliente").value = dataCliente.nombre || "";
            document.getElementById("resOrigen").value = dataCliente.direccion || "";
            document.getElementById("resCliente").setAttribute("readonly", true);
            document.getElementById("resOrigen").setAttribute("readonly", true);
            mostrarToast("✅ Cliente encontrado.", "success");
          } else {
            document.getElementById("resCliente").removeAttribute("readonly");
            document.getElementById("resOrigen").removeAttribute("readonly");
            document.getElementById("resCliente").value = "";
            document.getElementById("resOrigen").value = "";
            mostrarToast("ℹ️ Cliente nuevo. Ingresa los datos.", "info");
          }
        } catch (err) {
          console.error("Error buscando cliente:", err);
          mostrarToast("❌ No se pudo conectar al servidor", "error");
        }
      }
    });
  }

  // ---------------------------------------------------------
  // 5. FUNCIÓN CREAR RESERVA (Corregido cierre de modal)
  // ---------------------------------------------------------
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
      const dataCliente = await apiFetch(`/clientes/telefono/${telefono}`);

      if (dataCliente && dataCliente.existe) {
        clienteId = dataCliente.id_cliente;
      } else {
        const nuevoClienteData = await apiFetch("/clientes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ telefono, nombre: clienteNombre, direccion: origen })
        });

        if (nuevoClienteData && !nuevoClienteData.error) {
          clienteId = nuevoClienteData.id_cliente;
        } else {
          mostrarToast(nuevoClienteData?.error || "❌ Error al registrar cliente", "error");
          return;
        }
      }

      const dataReserva = await apiFetch("/reservas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cliente_id: clienteId, origen, destino, fecha, hora, estado: "activo" })
      });

      if (dataReserva && !dataReserva.error) {
        mostrarToast(`✅ Reserva creada con ID: ${dataReserva.reserva.id_reserva}`, "success");
        
        // ✅ Cierre seguro usando la instancia global del modal
        if (window.modalReservaInstance) {
          window.modalReservaInstance.hide();
        }

        programarAlerta(dataReserva.reserva);
                
      } else {
        mostrarToast(dataReserva?.error || "❌ Error al crear la reserva", "error");
      }
    } catch (err) {
      console.error("Error creando reserva:", err);
      mostrarToast("❌ No se pudo conectar al servidor", "error");
    }
  }

  // 💡 Pedir permiso para notificaciones nativas al cargar la página
  if (typeof Notification !== "undefined" && Notification.permission !== "granted" && Notification.permission !== "denied") {
      Notification.requestPermission();
  }

  // ---------------------------------------------------------
  // 6. ALERTAS Y SOCKETS
  // ---------------------------------------------------------
  function programarAlerta(reserva) {
      const fechaHoraReserva = new Date(`${reserva.fecha}T${reserva.hora}`);
      const ahora = new Date();
      const msHastaReserva = fechaHoraReserva - ahora;
      const msHastaAlerta = msHastaReserva - (15 * 60 * 1000);

      if (msHastaReserva <= 0) return;

      if (msHastaAlerta > 0) {
          // ✅ Programar temporizador local en el navegador para los 15 min previos
          setTimeout(() => {
              const nombreCliente = reserva.cliente_nombre || reserva.cliente?.nombre || "Cliente";
              const textoAlerta = `⚠️ ALERTA: La reserva #${reserva.id_reserva} de ${nombreCliente} es a las ${reserva.hora}`;
              
              // 1. Toast visual dentro de la app
              mostrarToast(textoAlerta, "warning");
              
              // 2. Audio de notificación
              const beep = new Audio('/static/sounds/notification.mp3');
              beep.play().catch(() => console.log("Permiso de audio requerido por el navegador"));

              // 3. 🚀 Notificación nativa (Sale en Windows/Linux aunque esté en otra app)
              if (typeof Notification !== "undefined" && Notification.permission === "granted") {
                  new Notification("¡Alerta de Reserva Próxima! 🚗", {
                      body: textoAlerta,
                      icon: "/static/images/logo_taxi.png" // Opcional: ajusta o elimina si no usas icono
                  });
              }
          }, msHastaAlerta);

          console.log(`✅ Reserva #${reserva.id_reserva} programada localmente. Sonará la alerta en ${Math.round(msHastaAlerta / 60000)} minutos.`);
      } else {
          // Si la reserva se creó y faltan menos de 15 minutos para la hora pactada
          const nombreCliente = reserva.cliente_nombre || reserva.cliente?.nombre || "Cliente";
          const textoAlerta = `⏰ Alerta: Reserva #${reserva.id_reserva} de ${nombreCliente} en menos de 15 min (${reserva.hora})`;
          
          mostrarToast(textoAlerta, "warning");
          
          const beep = new Audio('/static/sounds/notification.mp3');
          beep.play().catch(() => console.log("Permiso de audio requerido"));

          if (typeof Notification !== "undefined" && Notification.permission === "granted") {
              new Notification("¡Alerta de Reserva Próxima! 🚗", {
                  body: textoAlerta
              });
          }
      }
  }

  if (typeof socket !== 'undefined') {
    socket.on("reserva_activa", (data) => {
        const textoServidor = `🚗 ALERTA (Servidor): Reserva #${data.id_reserva} de ${data.cliente} está próxima (a las ${data.hora})`;
        mostrarToast(textoServidor, "info");
        
        const beep = new Audio('/static/sounds/notification.mp3');
        beep.play().catch(() => console.log("Permiso de audio requerido"));

        if (typeof Notification !== "undefined" && Notification.permission === "granted") {
            new Notification("Aviso del Servidor - Reserva 🚗", {
                body: textoServidor
            });
        }
    });
  }

  // ---------------------------------------------------------
  // 7. CARGAR RESERVAS EN TABLA
  // ---------------------------------------------------------
 // ---------------------------------------------------------
  // CARGAR RESERVAS POR VENCER (Pestaña Urgentes)
  // ---------------------------------------------------------
  async function cargarReservasPorVencer() {
      try {
        const data = await apiFetch("/reservas/por_vencer"); 
        const tbody = document.querySelector("#tablaReservasPorVencer tbody");
        if (!tbody) return; 
        
        tbody.innerHTML = "";
        const activas = (data && Array.isArray(data.reservas)) ? data.reservas : [];

        if (activas.length > 0) {
          activas.forEach(r => {
            const tr = document.createElement("tr");
           tr.innerHTML = `
              <td>${r.id_reserva}</td>
              <td>${r.cliente_telefono || r.cliente?.telefono || "—"}</td>
              <td>${r.cliente_nombre || r.cliente?.nombre || "—"}</td>
              <td>${r.origen}</td>
              <td>${r.destino}</td>
              <td>${r.fecha}</td>
              <td>${r.hora}</td>
            `;
            tbody.appendChild(tr);
          });
        } else {
          tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No hay reservas próximas a vencerse</td></tr>`;
        }
      } catch (err) {
        console.error("❌ Error cargando reservas por vencer:", err);
      }
  }

  // ---------------------------------------------------------
  // CARGAR AGENDA GENERAL (Pestaña Todas las Activas)
  // ---------------------------------------------------------
  async function cargarAgendaGeneral() {
      try {
        const data = await apiFetch("/reservas/activas"); 
        const tbody = document.querySelector("#tablaReservasAgenda tbody");
        if (!tbody) return; 
        
        tbody.innerHTML = "";
        const activas = (data && Array.isArray(data.reservas)) ? data.reservas : [];

        if (activas.length > 0) {
          activas.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td>${r.id_reserva}</td>
              <td>${r.cliente_telefono || r.cliente?.telefono || "—"}</td>
              <td>${r.cliente_nombre || r.cliente?.nombre || "—"}</td>
              <td>${r.origen}</td>
              <td>${r.destino}</td>
              <td>${r.fecha}</td>
              <td>${r.hora}</td>
            `;
            tbody.appendChild(tr);
          });
        } else {
          tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No hay reservas activas registradas</td></tr>`;
        }
      } catch (err) {
        console.error("❌ Error cargando agenda general:", err);
      }
  }

  // Cargar automáticamente las urgentes al abrir con Ctrl + R por defecto
  // y enganchar eventos de cambio de pestaña
  document.addEventListener("shown.bs.modal", (event) => {
    if (event.target.id === "modalListaReservas") {
      cargarReservasPorVencer(); // Carga inicial por defecto
    }
  });

  const tabAgendaBtn = document.getElementById("tab-agenda");
  if (tabAgendaBtn) {
    tabAgendaBtn.addEventListener("shown.bs.tab", () => {
      cargarAgendaGeneral();
    });
  }

  const tabUrgentesBtn = document.getElementById("tab-urgentes");
  if (tabUrgentesBtn) {
    tabUrgentesBtn.addEventListener("shown.bs.tab", () => {
      cargarReservasPorVencer();
    });
  }

  // ---------------------------------------------------------
  // 8. ENGANCHAR BOTÓN GUARDAR
  // ---------------------------------------------------------
  const btnCrearReserva = document.getElementById("btnCrearReserva");
  if (btnCrearReserva) {
    btnCrearReserva.addEventListener("click", crearReserva);
  }
});
// 🔄 VERIFICACIÓN POST-REINICIO: Al cargar la página, comprobar si hay reservas urgentes en la BD
  async function verificarReservasAlCargar() {
      try {
          const data = await apiFetch("/reservas/por_vencer");
          const activas = (data && Array.isArray(data.reservas)) ? data.reservas : [];
          
          const ahora = new Date();

          activas.forEach(r => {
              const fechaHoraReserva = new Date(`${r.fecha}T${r.hora}`);
              const msHastaReserva = fechaHoraReserva - ahora;
              
              // Si la reserva es para dentro de menos de 15 minutos (o ya pasó y sigue activa)
              if (msHastaReserva <= (15 * 60 * 1000) && msHastaReserva > 0) {
                  const nombreCliente = r.cliente_nombre || r.cliente?.nombre || "Cliente";
                  const textoAlerta = `⚠️ ALERTA (Recuperada): La reserva #${r.id_reserva} de ${nombreCliente} es a las ${r.hora}`;
                  
                  mostrarToast(textoAlerta, "warning");
                  
                  const beep = new Audio('/static/sounds/notification.mp3');
                  beep.play().catch(() => {});

                  if (typeof Notification !== "undefined" && Notification.permission === "granted") {
                      new Notification("¡Alerta de Reserva Pendiente! 🚗", { body: textoAlerta });
                  }
              }
          });
      } catch (err) {
          console.error("Error al verificar reservas tras reinicio:", err);
      }
  }