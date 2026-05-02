// ===============================================
// LÓGICA DE GESTIÓN DE CLIENTES
// ===============================================

// 1. Cargar la lista inicial de clientes
async function cargarClientes() {
    try {
        const response = await fetch('/api/v1/clientes/'); // GET /clientes/
        if (!response.ok) throw new Error('Error al cargar clientes');
        
        const clientes = await response.json();
        renderizarTablaClientes(clientes);
    } catch (error) {
        console.error("Error al cargar clientes:", error);
        alert("No se pudieron cargar los clientes.");
    }
}

// 2. Renderizar la tabla (Usando los datos de tu modelo)
function renderizarTablaClientes(clientes) {
    const tbody = document.getElementById('clientesBody');
    tbody.innerHTML = ''; // Limpiar contenido previo
    
    clientes.forEach(cliente => {
        const row = tbody.insertRow();
        
        // 🔴 ALERTA VISUAL: Si el cliente está bloqueado, cambiamos el diseño de la fila
        if (cliente.bloqueado) {
            row.className = 'bg-red-100 border-l-4 border-red-600 text-red-900 font-semibold';
        }
        
        row.insertCell().textContent = cliente.id_cliente;
        row.insertCell().textContent = cliente.nro_telefono || cliente.telefono;
        
        // Celda del Nombre con badge de alerta si está vetado
        const celdaNombre = row.insertCell();
        celdaNombre.textContent = cliente.nombre;
        
        if (cliente.bloqueado) {
            const badge = document.createElement('span');
            badge.className = 'ml-2 bg-red-600 text-white text-xs px-2 py-0.5 rounded font-bold uppercase animate-pulse';
            badge.textContent = 'Vetado';
            badge.title = cliente.motivo_bloqueo || 'Este cliente tiene una restricción administrativa';
            celdaNombre.appendChild(badge);
        }

        row.insertCell().textContent = cliente.direccion || 'N/A';
        row.insertCell().textContent = cliente.punto_referencia || 'Ninguna';

        // Celda de Acciones
        const accionesCell = row.insertCell();
        
        if (cliente.bloqueado) {
            // Mostramos el motivo en lugar de los botones para que el operador decida
            const spanMotivo = document.createElement('span');
            spanMotivo.className = 'text-xs text-red-700 italic font-bold';
            spanMotivo.textContent = `🚫 No atender: ${cliente.motivo_bloqueo || 'Restringido'}`;
            accionesCell.appendChild(spanMotivo);
        } else {
            // Botón Editar
            const btnEditar = document.createElement('button');
            btnEditar.textContent = 'Editar';
            btnEditar.className = 'bg-yellow-500 text-white px-2 py-1 rounded mr-2';
            btnEditar.onclick = () => editarCliente(cliente);
            accionesCell.appendChild(btnEditar);
            
            // Botón Eliminar
            const btnEliminar = document.createElement('button');
            btnEliminar.textContent = 'Eliminar';
            btnEliminar.className = 'bg-red-500 text-white px-2 py-1 rounded';
            btnEliminar.onclick = () => confirmarEliminarCliente(cliente.id_cliente, cliente.nombre);
            accionesCell.appendChild(btnEliminar);
        }
    });
}
// 4. Abrir Modal (Crear o Editar)
let modoModal = 'crear'; // Variable global para saber si estamos creando o editando

function abrirModalCliente(cliente = null) {
    const modal = document.getElementById('modalCliente');
    const titulo = document.getElementById('modalClienteTitulo');
    
    document.getElementById('clienteId').value = '';
    document.getElementById('clienteTelefono').value = '';
    document.getElementById('clienteNombre').value = '';
    document.getElementById('clienteDireccion').value = '';
    document.getElementById('clienteReferencia').value = '';

    if (cliente) {
        modoModal = 'editar';
        titulo.textContent = 'Modificar Cliente';
        document.getElementById('clienteId').value = cliente.id_cliente;
        document.getElementById('clienteTelefono').value = cliente.telefono;
        document.getElementById('clienteNombre').value = cliente.nombre;
        document.getElementById('clienteDireccion').value = cliente.direccion || '';
        document.getElementById('clienteReferencia').value = cliente.punto_referencia || '';
        document.getElementById('clienteTelefono').disabled = true; // No se edita el teléfono en este modal
    } else {
        modoModal = 'crear';
        titulo.textContent = 'Registrar Nuevo Cliente';
        document.getElementById('clienteTelefono').disabled = false;
    }
    
    modal.classList.remove('hidden');
}

function cerrarModalCliente() {
    document.getElementById('modalCliente').classList.add('hidden');
}

// 5. Guardar Cliente (POST o PUT)
async function guardarCliente() {
    const id = document.getElementById('clienteId').value;
    const telefono = document.getElementById('clienteTelefono').value;
    const nombre = document.getElementById('clienteNombre').value;
    const direccion = document.getElementById('clienteDireccion').value;
    const punto_referencia = document.getElementById('clienteReferencia').value;

    const data = { telefono, nombre, direccion, punto_referencia };
    let url, method;

    if (modoModal === 'crear') {
        url = '/api/v1/clientes/';
        method = 'POST';
    } else {
        // Usamos la ruta PUT que actualiza por teléfono, no por ID
        // Nota: Si usaras la ruta de actualizar_cliente_por_telefono, la URL sería diferente
        url = `/api/v1/clientes/telefono/${telefono}`; 
        method = 'PUT';
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            cerrarModalCliente();
            cargarClientes(); // Recargar la lista
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error("Error al guardar cliente:", error);
        alert("Error de conexión al guardar cliente.");
    }
}

// 6. Eliminar Cliente (DELETE)
function confirmarEliminarCliente(id, nombre) {
    if (confirm(`¿Está seguro de eliminar al cliente ${nombre} (ID: ${id})?`)) {
        fetch(`/api/v1/clientes/${id}`, {
            method: 'DELETE',
            // headers: { 'Authorization': 'Bearer ' + tuTokenJWT }
        })
        .then(response => {
            if (response.ok) {
                alert(`Cliente ${nombre} eliminado.`);
                cargarClientes();
            } else {
                response.json().then(error => alert('Error al eliminar: ' + error.error));
            }
        })
        .catch(err => console.error("Error al eliminar:", err));
    }
}

// 7. Lógica de inicio (Asegúrate de que esta función se llama cuando se carga el menú)
function cargarContenido(modulo) {
    // Código para ocultar todos los contenidos y mostrar solo el del módulo
    
    if (modulo === 'clientes') {
        cargarClientes(); // Carga los datos cuando se selecciona "Clientes"
    }
    // ... otros módulos
}

// Carga inicial al iniciar la aplicación (Asumiendo que despachos es el inicio)
document.addEventListener('DOMContentLoaded', () => {
    // ... código de inicialización
    cargarContenido('despachos'); // O el módulo que desees como vista principal
});