// ===============================
// modales_iterativo.js
// Modal Despacho Múltiple en modo iteración (sin bloques dinámicos)
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DOMContentLoaded (modales_iterativo.js)");

  let totalIteraciones = 0;
  let iteracionActual = 0;
  let grupoIdGlobal = null;
  
  function iniciarDespachoMultiple(iteraciones) {
    totalIteraciones = iteraciones;
    iteracionActual = 0;
    grupoIdGlobal = "grupo-" + Date.now();
  }


  // Mantener registro de conductores/autos ya usados en el grupo (opcional)
  const usados = {
    conductores: new Set(),
    autos: new Set()
  };

  // -------------------------------
  // Inicializar ciclo múltiple al seleccionar tipo
  // -------------------------------
  // Dentro del DOMContentLoaded que ya tienes en modales.js
  const tipo = document.getElementById("tipoDespacho");
    if (tipo) {
      tipo.addEventListener("change", async () => {
          const val = tipo.value;

          if (["2","3","4"].includes(val)) {
            const conductores = await cargarConductoresYAutosDespachoMultiple();
            if (!Array.isArray(conductores) || conductores.length < parseInt(val, 10)) {
              mostrarToast(`🚦 No hay suficientes conductores → se requieren ${val}, disponibles: ${conductores?.length || 0}`, "error");
              return;
            }

            iniciarDespachoMultiple(parseInt(val, 10));
            usados.conductores.clear();
            usados.autos.clear();

            const modalEl = document.getElementById("modalDespachoMultiple");
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
          }
        });
    }

  // -------------------------------
  // Crear despacho iterado
  // -------------------------------
  
  const btnGuardar = document.getElementById("btnGuardarDespacho");
  if (btnGuardar) btnGuardar.addEventListener("click", crearDespachoIterado);
  
  async function crearDespachoIterado(e) {
      e.preventDefault();

      const origen = document.getElementById("modalOrigen").value.trim();
      const destino = document.getElementById("modalDestino").value.trim();
      const tarifa = parseFloat(document.getElementById("modalTarifa").value || 0);
      const clienteId = parseInt(document.getElementById("clienteIdHidden").value || 0);
      const conductorId = parseInt(document.getElementById("modalConductor").value || 0);
      const autoId = parseInt(document.getElementById("modalAuto").value || 0);

      const despacho = {
        origen_despacho: origen,
        destino_despacho: destino,
        cliente_id: clienteId,
        conductor_id: conductorId,
        auto_id: autoId,
        tarifa,
        estado_despacho: "en curso",
        grupo_id: grupoIdGlobal
      };

      const res = await apiFetch("/despachos", {
        method: "POST",
        body: JSON.stringify(despacho),
        headers: { "Content-Type": "application/json" }
      });

      if (res.ok) {
        mostrarToast("✅ Despacho creado correctamente, continue con el siguiente", "success");
        iteracionActual++;
        if (iteracionActual >= totalIteraciones) {
          bootstrap.Modal.getInstance(document.getElementById("modalDespachoMultiple")).hide();
          mostrarToast("🎯 Iteración completa, modal cerrado", "info");
        }
      } else {
        mostrarToast("❌ Error al crear despacho", "error");
      }
    }


  // -------------------------------
  // Limpieza de variables entre iteraciones
  // -------------------------------
  function limpiarCamposVariables() {
    document.getElementById("modalConductor").value = "";
    document.getElementById("modalAuto").value = "";
    document.getElementById("modalDestino").value = "";
    document.getElementById("modalTarifa").value = "";
  }
  async function cargarConductoresYAutosDespachoMultiple() {
    try {
      const res = await apiFetch("/conductores/activos_con_autos"); // 👈 nuevo endpoint
      const data = await res.json();

      const conductorSelect = document.getElementById("modalConductor");
      const autoSelect = document.getElementById("modalAuto");

      conductorSelect.innerHTML = "<option value='' disabled selected>Seleccione...</option>";
      autoSelect.innerHTML = "<option value='' disabled selected>Seleccione...</option>";

      if (Array.isArray(data) && data.length > 0) {
        data.forEach(t => {
          if (t.auto) {
            // Poblar conductores
            const optConductor = document.createElement("option");
            optConductor.value = t.conductor.id_conductor;
            optConductor.textContent = `${t.conductor.codigo} - ${t.conductor.nombre}`;
            conductorSelect.appendChild(optConductor);

            // Poblar autos
            const optAuto = document.createElement("option");
            optAuto.value = t.auto.id_auto;
            optAuto.textContent = `${t.auto.nro_placa} - ${t.auto.marca} ${t.auto.modelo}`;
            autoSelect.appendChild(optAuto);
          }
        });

        // 🔹 Sincronizar conductor → auto
        conductorSelect.addEventListener("change", (e) => {
          const conductorId = parseInt(e.target.value, 10);
          const encontrado = data.find(t => t.conductor.id_conductor === conductorId);
          if (encontrado && encontrado.auto) {
            autoSelect.value = encontrado.auto.id_auto;
            console.log("🚗 Auto sincronizado automáticamente:", autoSelect.value);
          }
        });
      } else {
        const opt = document.createElement("option");
        opt.disabled = true;
        opt.textContent = "No hay conductores disponibles";
        conductorSelect.appendChild(opt);
        autoSelect.appendChild(opt.cloneNode(true));
      }

      return data;
    } catch (err) {
      console.error("❌ Error cargando conductores/autos:", err);
      mostrarToast("❌ No se pudo cargar la lista de conductores/autos", "error");
    }
  }




    // -------------------------------
  // Inicializar modal múltiple
  // -------------------------------
  async function onShowModalOnce() {
    // 🔹 Poblar conductores y autos en un solo paso
    await cargarConductoresYAutosDespachoMultiple();

    const selectConductor = document.getElementById("modalConductor");
    const autoSelect = document.getElementById("modalAuto");

    // Seleccionar automáticamente el primer conductor válido
    const firstValidOption = Array.from(selectConductor.options).find(opt => opt.value);
    if (firstValidOption && !selectConductor.disabled) {
      selectConductor.value = firstValidOption.value;
      console.log("🧩 Conductor seleccionado automáticamente:", selectConductor.value);

      // Sincronizar auto correspondiente
      const data = await apiFetch("/conductores/en_turno_disponibles").then(r => r.json());
      const encontrado = data.find(t => t.conductor.id_conductor === parseInt(selectConductor.value, 10));
      if (encontrado && encontrado.auto) {
        autoSelect.value = encontrado.auto.id_auto;
        console.log("🚗 Auto sincronizado automáticamente:", autoSelect.value);
      }
    }
  }

// -------------------------------
// Listener de Bootstrap al mostrar modal
// -------------------------------
document.addEventListener("shown.bs.modal", async (e) => {
  if (e.target.id === "modalDespachoMultiple") {
    console.log("🟢 Modal múltiple mostrado");
    await onShowModalOnce();
  }
});


  // -------------------------------
  // Enganchar al evento de Bootstrap
  // -------------------------------
  document.addEventListener("shown.bs.modal", async (e) => {
    if (e.target.id === "modalDespachoMultiple") {
      console.log("🟢 Modal múltiple mostrado");
      await onShowModalOnce();
    }
  });

 


  // -------------------------------
// 📌 Listener de teléfono en modal múltiple
// -------------------------------
  const telefonoInput = document.getElementById("modalTelefono");
  if (telefonoInput) {
    telefonoInput.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const telefono = telefonoInput.value.trim();
        const regexTelefono = /^(0276|0412|0414|0416|0424|0426)[0-9]{7}$/;

        if (!regexTelefono.test(telefono)) {
          mostrarToast("⚠️ Número de teléfono inválido.", "error");
          return;
        }

        try {
          const resCliente = await apiFetch(`/clientes/telefono/${telefono}`);
          const dataCliente = await resCliente.json();
          // 🔹 Blindaje: asegurar que el hidden exista SIEMPRE
          let hidden = document.getElementById("clienteIdHidden");
          if (!hidden) {
            hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.id = "clienteIdHidden";
            hidden.name = "clienteIdHidden";

            const form = document.getElementById("formModalDespacho");
            if (form) {
              form.appendChild(hidden);
              console.log("✅ clienteIdHidden creado dinámicamente dentro del formulario");
            } else {
              console.error("❌ No se encontró formModalDespacho para insertar el hidden");
            }
          }
          if (resCliente.ok && dataCliente.existe) {
            const hidden = document.getElementById("clienteIdHidden");
            if (hidden) {
              hidden.value = dataCliente.id_cliente;
            } else {
              console.error("❌ clienteIdHidden no existe en el DOM en este momento");
            }
            // Cliente existente → llenar y bloquear campos comunes
            //document.getElementById("clienteIdHidden").value = dataCliente.id_cliente;
            document.getElementById("modalCliente").value = dataCliente.nombre || "";
            document.getElementById("modalOrigen").value = dataCliente.direccion || "";
            document.getElementById("modalCliente").setAttribute("readonly", true);
            document.getElementById("modalOrigen").setAttribute("readonly", true);
            window.clienteIdActual = dataCliente.id_cliente;
            mostrarToast("✅ Cliente encontrado. Completa destino y tarifa.", "success");
          } else {
            // Cliente nuevo → habilitar edición
            document.getElementById("clienteIdHidden").value = 0;
            document.getElementById("modalCliente").removeAttribute("readonly");
            document.getElementById("modalOrigen").removeAttribute("readonly");
            document.getElementById("modalCliente").value = "";
            document.getElementById("modalOrigen").value = "";
            window.clienteIdActual = null;
            mostrarToast("ℹ️ Cliente nuevo. Ingresa todos los datos.", "info");
          }
        } catch (err) {
          console.error("❌ Error buscando cliente:", err);
          mostrarToast("❌ No se pudo conectar al servidor", "error");
        }
      }
    });
  }

});
