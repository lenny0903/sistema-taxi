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
    const btnEnviar = document.getElementById('btnEnviarDespacho');

    if (!telefonoInput) return;

    // 1. Validar formato antes de ir al servidor
    // Usamos la misma lógica que tu HTML: 0276... o 04...
    const regexTelefono = /^(0276[0-9]{7}|04[0-9]{9})$/;
    const telefono = telefonoInput.value.trim();

    if (!telefono) return;

    if (!regexTelefono.test(telefono)) {
        // En lugar de ir al servidor, avisamos al usuario
        if (typeof mostrarToast === 'function') {
            mostrarToast("⚠️ Formato inválido. Use 11 dígitos (0276... o 04...)", "error");
        }
        telefonoInput.classList.add("border-red-500"); // Feedback visual
        return; // Salimos de la función, no gastamos recursos del servidor
    } else {
        telefonoInput.classList.remove("border-red-500");
    }

    // 2. Si pasó la validación, procedemos con el fetch
    try {
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

            if (btnEnviar) {
                setTimeout(() => btnEnviar.focus(), 100); 
            }
            
        } else {
            if (btnModificar) btnModificar.disabled = true;
            if (window.activarCamposDespacho) activarCamposDespacho(false);
            abrirModalCliente(telefono, null); 
        }
    } catch (err) {
        console.error("Error al buscar cliente:", err);
        // Aquí podrías mostrar un toast si el servidor falla por otra razón
    }
}

// Exponer globalmente
window.validarClientePorTelefono = validarClientePorTelefono;
window.abrirModalCliente = abrirModalCliente;