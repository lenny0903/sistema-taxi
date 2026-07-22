// ===============================
// Módulo Despacho Múltiple
// ===============================

// 1. Validar disponibilidad
export function validarDisponibilidadVehiculos(nroSolicitados, pilaDisponibles) {
  if (nroSolicitados <= 0) {
    mostrarToast("Debe solicitar al menos un vehículo", "error");
    return false;
  }
  if (nroSolicitados > pilaDisponibles.length) {
    mostrarToast("No hay suficientes conductores/autos disponibles", "error");
    return false;
  }
  mostrarToast("Disponibilidad confirmada", "info");
  return true;
}

// 2. Cargar datos comunes
export function cargarDatosComunes(cliente, origen, tarifa, destino) {
  return {
    cliente,
    origen,
    tarifa,
    destino
  };
}

// 3. Crear despacho múltiple
export function crearDespachoMultiple(datosComunes, conductor, auto) {
  const despacho = {
    ...datosComunes,
    conductor,
    auto,
    estado: "Activo"
  };
  // Aquí iría la llamada al backend (API REST)
  console.log("Despacho creado:", despacho);
  mostrarToast(`Despacho creado: ${conductor} - ${auto}`, "info");
  return despacho;
}

// 4. Actualizar selects dinámicos
export function actualizarSelectsDisponibles(pilaDisponibles) {
  const selectConductor = document.getElementById("desConductor");
  const selectAuto = document.getElementById("desAuto");

  // Limpiar
  selectConductor.innerHTML = "";
  selectAuto.innerHTML = "";

  // Rellenar con disponibles
  pilaDisponibles.forEach(item => {
    const optCon = document.createElement("option");
    optCon.value = item.conductor;
    optCon.textContent = item.conductor;
    selectConductor.appendChild(optCon);

    const optAuto = document.createElement("option");
    optAuto.value = item.auto;
    optAuto.textContent = item.auto;
    selectAuto.appendChild(optAuto);
  });
}

// 5. Feedback centralizado
export function mostrarToast(mensaje, tipo="info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.textContent = mensaje;
  toast.className = `toast-${tipo}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
