/**
 * Busca un conductor por cédula y llena el formulario base.
 * Se activa al presionar Enter en el campo de cédula.
 */
// En static/js/conductores.js

function seleccionarConductor(c) {
    console.log("Conductor seleccionado:", c);
    
    // Poblamos el formulario de conductores
    document.getElementById('conId').value = c.id_conductor;
    document.getElementById('conCedula').value = c.nro_cedula;
    document.getElementById('conNombre').value = c.nombre;
    document.getElementById('conCodigo').value = c.codigo;
    document.getElementById('conTelefono').value = c.nro_telefono;

    // Cambiamos el botón a modo edición (Azul)
    const btn = document.getElementById('btnGuardarConductor');
    if (btn) {
        btn.textContent = "Actualizar Cambios";
        btn.classList.replace('bg-green-500', 'bg-blue-600');
    }
}

// ESTA LÍNEA ES LA QUE SOLUCIONA EL ERROR:
window.seleccionarConductor = seleccionarConductor;
async function validarConductor() {
    const cedula = document.getElementById('conCedula').value.trim();
    if (!cedula) return;

    try {
        // 1. Petición limpia (sin res.ok ni res.json)
        const data = await apiFetch(`/conductores/buscar?nro_cedula=${cedula}`);
        
        // 2. Lógica de negocio sobre la data recibida
        if (data && data.length > 0) {
            const c = data[0]; 

            // Llenamos el formulario
            document.getElementById('conId').value = c.id_conductor;
            document.getElementById('conNombre').value = c.nombre;
            document.getElementById('conCodigo').value = c.codigo;
            document.getElementById('conTelefono').value = c.nro_telefono;

            // Feedback visual amigable con TU función
            mostrarToast(`✅ Conductor encontrado: ${c.nombre}`, 'success');

            // Cambiar a modo edición
            const btn = document.getElementById('btnGuardarConductor');
            if (btn) {
                btn.textContent = "Actualizar Cambios";
                btn.classList.replace('bg-green-500', 'bg-blue-600');
            }
            
            document.getElementById('conNombre').focus();
        } else {
            // Caso: Lista vacía []
            mostrarToast("ℹ️ Cédula no registrada. Preparando formulario para nuevo ingreso.", 'info');
            resetearFormConductor(false);
        }

    } catch (err) {
        // 3. Manejo de errores de red o servidor
        console.error("Error en validación:", err.message);
        
        // Extraemos el mensaje real para el Toast
        const msg = err.message.includes('{') 
                    ? JSON.parse(err.message.substring(err.message.indexOf('{'))).error 
                    : err.message;

        mostrarToast("📍 " + msg, 'error');
    }
}
// Escuchador de Tecla Enter
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && e.target.id === 'conCedula') {
        e.preventDefault();
        validarConductor();
    }
});

function resetearFormConductor(todo) {
    if (todo) document.getElementById('conCedula').value = "";
    document.getElementById('conId').value = "";
    document.getElementById('conNombre').value = "";
    document.getElementById('conCodigo').value = "";
    document.getElementById('conTelefono').value = "";
    
    const btn = document.getElementById('btnGuardarConductor');
    if (btn) {
        btn.textContent = "Guardar";
        btn.classList.add('bg-green-500');
        btn.classList.remove('bg-blue-600');
    }
}// Asegúrate de que guardarConductor use nro_telefono para que Python lo entienda
async function guardarConductor(e) {
    if (e) e.preventDefault();
    
    const id = document.getElementById('conId').value;
    const datos = {
        nro_cedula: document.getElementById('conCedula').value,
        nombre: document.getElementById('conNombre').value,
        codigo: document.getElementById('conCodigo').value,
        nro_telefono: document.getElementById('conTelefono').value
    };

    const metodo = id ? 'PUT' : 'POST';
    const url = id ? `/conductores/${id}` : '/conductores';

    try {
        // 1. Llamada limpia. Si falla (400), saltará al catch automáticamente.
        const data = await apiFetch(url, {
            method: metodo,
            body: JSON.stringify(datos)
        });

        // 2. ÉXITO: Si llega aquí, todo salió bien
        mostrarToast(id ? "✅ Conductor actualizado con éxito" : "✅ Conductor registrado correctamente", 'success');
        
        resetearFormConductor(true);
        if (typeof cargarConductores === 'function') cargarConductores();

    } catch (err) {
        // 3. MANEJO DE ERRORES AMIGABLE (Adiós al pánico)
        console.error("Error al guardar:", err.message);

        // Extraemos el mensaje del JSON que nos mostró tu consola (ej: "El código ya está registrado")
        let mensajeParaUsuario = err.message;
        
        if (err.message.includes('{')) {
            try {
                const errorObj = JSON.parse(err.message.substring(err.message.indexOf('{')));
                mensajeParaUsuario = errorObj.error || errorObj.msg;
            } catch (e) { /* fallback al original */ }
        }

        // Mostramos el Toast rojo con la explicación exacta del servidor
        mostrarToast("⚠️ No se pudo guardar: " + mensajeParaUsuario, 'error');
    }
}

function resetearFormConductor(limpiarTodo) {
    if (limpiarTodo) document.getElementById('conCedula').value = "";
    
    document.getElementById('conId').value = "";
    document.getElementById('conNombre').value = "";
    document.getElementById('conCodigo').value = "";
    document.getElementById('conTelefono').value = "";
    
    const btn = document.getElementById('btnGuardarConductor');
    btn.textContent = "Guardar";
    btn.classList.remove('bg-blue-600');
    btn.classList.add('bg-green-500');
}

// Inicialización de eventos
document.addEventListener('DOMContentLoaded', () => {
    const inputCedula = document.getElementById('conCedula');
    const form = document.getElementById('formConductor');

    if (inputCedula) {
        inputCedula.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); 
                validarConductor();
            }
        });
    }

    if (form) {
        form.addEventListener('submit', guardarConductor);
    }
});
