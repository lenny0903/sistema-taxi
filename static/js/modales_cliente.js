// ==================== Validar cliente por teléfono ====================
async function validarClientePorTelefono() {
  const telefono = document.getElementById('desTelefono').value.trim();
  if (!telefono) return null;

  const clientes = await fetchDefensivo(`/clientes/buscar?telefono=${telefono}`);
  const cliente = clientes.length > 0 ? clientes[0] : null;

  if (cliente) {
    document.getElementById('desNombre').value = cliente.nombre || '';
    document.getElementById('desOrigen').value = cliente.direccion || '';
    activarCamposDespacho(true);
    return cliente;
  } else {
    document.getElementById('desNombre').value = '';
    document.getElementById('desOrigen').value = '';
    activarCamposDespacho(false);
    abrirModalCrearCliente(telefono);
    return null;
  }
}

window.validarClientePorTelefono = validarClientePorTelefono;


// Exponer globalmente
window.validarClientePorTelefono = validarClientePorTelefono;



// ==================== Modal Crear Cliente ====================
// ==================== Modal Crear Cliente ====================
function abrirModalCrearCliente(telefono) {
  const modal = document.getElementById("modalCrearCliente");
  modal.classList.remove("hidden");

  document.getElementById("btnGuardarCliente").onclick = async () => {
    const nombre = document.getElementById("nuevoClienteNombre").value.trim();
    const direccion = document.getElementById("nuevoClienteDireccion").value.trim();

    if (!validarNombre(nombre)) {
      alert("❌ Nombre inválido.");
      return;
    }

    const nuevoCliente = { telefono, nombre, direccion };
    const resPost = await apiFetch("/clientes/", {
      method: "POST",
      body: JSON.stringify(nuevoCliente)
    });

    const result = await resPost.json();
    if (resPost.ok) {
      mostrarToast("✅ Cliente creado correctamente", "info");
      // 👉 rellenar formulario base completo
      document.getElementById('desTelefono').value = telefono;
      document.getElementById('desNombre').value = nombre;
      document.getElementById('desOrigen').value = direccion;
      activarCamposDespacho(true);
    } else {
      mostrarToast("❌ Error al crear cliente: " + (result.error || "verifica datos"), "error");
    }

    cerrarModalCrearCliente(); // 👉 cerrar modal al guardar
  };

  document.getElementById("btnCancelarModal").onclick = cerrarModalCrearCliente;
}

function cerrarModalCrearCliente() {
  const modal = document.getElementById("modalCrearCliente");
  modal.classList.add("hidden");
}

// ==================== Exponer funciones globalmente ====================
window.validarClientePorTelefono = validarClientePorTelefono;
window.abrirModalCrearCliente = abrirModalCrearCliente;
window.cerrarModalCrearCliente = cerrarModalCrearCliente;
