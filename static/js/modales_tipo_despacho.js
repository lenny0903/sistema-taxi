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
      // 1. 🛡️ LIMPIEZA: Si ya existe una instancia previa en este elemento, la eliminamos
      const existingInstance = bootstrap.Modal.getInstance(modalReserva);
      if (existingInstance) {
          existingInstance.dispose();
          console.log("♻️ Instancia previa de modalReserva descartada para liberar memoria");
      }

      // 2. 🏗️ CREACIÓN: Creamos la instancia limpia
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
        event.preventDefault(); // Evita que se recargue o se envíe el form
        
        const telefono = telefonoInput.value.trim();
        
        // 1. VALIDACIÓN: Si está vacío, no hacemos nada (ignora el Enter)
        if (telefono === "") {
            console.log("Input vacío, se ignora el Enter.");
            return;
        }

        // 2. VALIDACIÓN DE FORMATO
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
        // 1. Buscar cliente (apiFetch ya devuelve el JSON)
        const dataCliente = await apiFetch(`/clientes/telefono/${telefono}`);

        if (dataCliente && dataCliente.existe) {
          clienteId = dataCliente.id_cliente;
        } else {
          // 2. Registrar nuevo cliente si no existe
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

        // 3. Crear la reserva
        const dataReserva = await apiFetch("/reservas", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cliente_id: clienteId, origen, destino, fecha, hora, estado: "activo" })
        });

        if (dataReserva && !dataReserva.error) {
          mostrarToast(`✅ Reserva creada con ID: ${dataReserva.reserva.id_reserva}`, "success");
          
          const modalElement = document.getElementById('modalReserva'); // Asegúrate que el ID coincida
          const instance = bootstrap.Modal.getInstance(modalElement);
          bootstrap.Modal.getInstance(modalReserva).hide();
          if (instance) instance.hide();

          programarAlerta(dataReserva.reserva);
                  
        } else {
          mostrarToast(dataReserva?.error || "❌ Error al crear la reserva", "error");
        }
      } catch (err) {
        console.error("Error creando reserva:", err);
        mostrarToast("❌ No se pudo conectar al servidor", "error");
      }
    }

  // -------------------------------
  // 📌 Programar alerta de reserva
  // -------------------------------
  // --- Lógica Local (Sigue funcionando para el operador actual) ---
  function programarAlerta(reserva) {
      const fechaHoraReserva = new Date(`${reserva.fecha}T${reserva.hora}`);
      const ahora = new Date();
      const msHastaReserva = fechaHoraReserva - ahora;
      const msHastaAlerta = msHastaReserva - (15 * 60 * 1000);

      if (msHastaReserva <= 0) return;

      if (msHastaAlerta > 0) {
          // En lugar de un setTimeout que se puede borrar, 
          // confiamos en que el Scheduler de Python avisará a todos por Socket.
          console.log(`Reserva #${reserva.id_reserva} programada. El servidor avisará a los 15 min.`);
      } else {
          // Si falta menos de 15 min justo cuando cargamos la lista, avisamos de una vez
          mostrarToast(`⏰ Alerta: Reserva #${reserva.id_reserva} en menos de 15 min`, "warning");
      }
  }

  // --- Lógica Global (Para todas las PCs de la oficina vía Socket) ---
  // Este evento debe coincidir con el nombre que emitas en scheduler.py
  socket.on("reserva_activa", (data) => {
      // IMPORTANTE: Aquí aplicamos tu misma lógica de los 15 minutos 
      // pero validada desde el servidor
      mostrarToast(
          `🚗 ALERTA: Reserva #${data.id_reserva} de ${data.cliente} está próxima (a las ${data.hora})`,
          "info"
      );
      
      // Sonido de alerta para la oficina
      const beep = new Audio('/static/sounds/notification.mp3');
      beep.play().catch(() => console.log("Permiso de audio requerido"));
  });

  // -------------------------------
  // 📌 Enganchar botones
  // -------------------------------
  const btnCrearReserva = document.getElementById("btnCrearReserva");
  if (btnCrearReserva) btnCrearReserva.addEventListener("click", crearReserva);
  
  ////Función cargar reservas en modal (por implementar)/////
  async function cargarReservasPorVencer() {
      try {
        // 1. apiFetch ya procesa el JSON. 'data' ya contiene el objeto con las reservas.
        const data = await apiFetch("/reservas/por_vencer"); 
        
        console.log("📡 Datos recibidos en reservas:", JSON.stringify(data, null, 2));

        const tbody = document.querySelector("#tablaReservas tbody");
        if (!tbody) return; // Seguridad por si el elemento no existe en el DOM
        
        tbody.innerHTML = "";

        // 2. Accedemos directamente a data.reservas (que es lo que envía tu Flask)
        const activas = (data && Array.isArray(data.reservas)) 
          ? data.reservas.filter(r => r.estado === "activo") 
          : [];

        if (activas.length > 0) {
          activas.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td>${r.id_reserva}</td>
              <td>${r.cliente_nombre || r.cliente?.nombre || "—"}</td>
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
        // Evitamos mostrar el toast cada vez que falle el polling para no molestar al usuario, 
        // a menos que sea una carga manual.
      }
    }


});
