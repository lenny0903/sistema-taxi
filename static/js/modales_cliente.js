// ==================== Función Unificada de Modal ====================
function abrirModalCliente(telefono, cliente = null) {
    const modal = document.getElementById("modalEditarCliente");
    if (!modal) return console.error("No se encontró el modalEditarCliente");

    const titulo = modal.querySelector("h2");
    const inputNombre = document.getElementById("modalNombre");
    const inputDireccion = document.getElementById("modalDireccion");

    // Configurar modo Editar o Crear
    if (cliente) {
        titulo.innerText = "Editar Cliente";
        inputNombre.value = cliente.nombre || '';
        inputDireccion.value = cliente.direccion || '';
    } else {
        titulo.innerText = "Nuevo Cliente";
        inputNombre.value = "";
        inputDireccion.value = "";
    }

    modal.classList.remove("hidden");

    // Configurar Guardar
    document.getElementById("btnGuardarModal").onclick = async () => {
        const nombre = inputNombre.value.trim();
        const direccion = inputDireccion.value.trim();

        if (!nombre || !direccion) {
            alert("Por favor complete nombre y dirección");
            return;
        }

        const metodo = cliente ? "PUT" : "POST";
        const url = cliente ? `/clientes/${cliente.id_cliente}` : "/clientes/";

        const res = await apiFetch(url, {
            method: metodo,
            body: JSON.stringify({ nombre, direccion, telefono })
        });

        if (res && !res.error) {
            mostrarToast(`✅ Cliente ${cliente ? 'actualizado' : 'creado'}`, "info");
            document.getElementById('desNombre').value = nombre;
            document.getElementById('desOrigen').value = direccion;
            if (window.activarCamposDespacho) activarCamposDespacho(true);
            modal.classList.add("hidden");
        }
    };

    document.getElementById("btnCancelarModal").onclick = () => {
        modal.classList.add("hidden");
    };
}

// ==================== Validación Principal ====================
async function validarClientePorTelefono() {
    const telefonoInput = document.getElementById('desTelefono');
    const btnModificar = document.getElementById('btnModificarCliente');
    const btnEnviar = document.getElementById('btnEnviarDespacho'); // Capturamos el botón enviar

    if (!telefonoInput) return;

    const telefono = telefonoInput.value.trim();
    if (!telefono) return;

    const resultado = await fetchDefensivo(`/clientes/buscar?telefono=${telefono}`);
    const cliente = (resultado && resultado.length > 0) ? resultado[0] : null;

    if (cliente) {
        document.getElementById('desNombre').value = cliente.nombre;
        document.getElementById('desOrigen').value = cliente.direccion;
        
        if (btnModificar) {
            btnModificar.disabled = false;
            btnModificar.onclick = () => abrirModalCliente(telefono, cliente);
        }
        
        if (window.activarCamposDespacho) activarCamposDespacho(true);

        // 🔥 LA CLAVE: Si el cliente existe, mandamos el foco al botón ENVIAR
        if (btnEnviar) {
            setTimeout(() => btnEnviar.focus(), 100); 
        }
        
    } else {
        if (btnModificar) btnModificar.disabled = true;
        if (window.activarCamposDespacho) activarCamposDespacho(false);
        abrirModalCliente(telefono, null); 
    }
}

// Exponer globalmente
window.validarClientePorTelefono = validarClientePorTelefono;
window.abrirModalCliente = abrirModalCliente;