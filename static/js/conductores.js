/**
 * CRUD de Conductores - Los Patriotas
 * Sistema de gestión robusto con búsqueda dual y validación de datos.
 */

// 1. POBLAR FORMULARIO (Modo Edición)
function seleccionarConductor(c) {
    console.log("Conductor seleccionado:", c);
    
    document.getElementById('conId').value = c.id_conductor;
    document.getElementById('conCedula').value = c.nro_cedula;
    document.getElementById('conNombre').value = c.nombre;
    document.getElementById('conCodigo').value = c.codigo;
    document.getElementById('conTelefono').value = c.nro_telefono;

    const btn = document.getElementById('btnGuardarConductor');
    if (btn) {
        btn.textContent = "Actualizar Cambios";
        btn.classList.replace('bg-green-500', 'bg-blue-600');
    }
}

// Globalizar para acceso desde tablas externas si es necesario
window.seleccionarConductor = seleccionarConductor;

// 2. RESETEAR FORMULARIO (Inteligente)
function resetearFormConductor(limpiarBusqueda = true) {
    if (limpiarBusqueda) {
        document.getElementById('conCedula').value = "";
        document.getElementById('conCodigo').value = "";
    }

    document.getElementById('conId').value = "";
    document.getElementById('conNombre').value = "";
    document.getElementById('conTelefono').value = "";

    const btn = document.getElementById('btnGuardarConductor');
    if (btn) {
        btn.textContent = "Guardar";
        btn.classList.add('bg-green-500');
        btn.classList.remove('bg-blue-600');
    }
}

// 3. VALIDAR / BUSCAR (Cédula o Código)
async function validarConductor() {
    const inputCedula = document.getElementById('conCedula');
    const inputCodigo = document.getElementById('conCodigo');
    
    const cedula = inputCedula.value.trim();
    const codigo = inputCodigo.value.trim();
    
    if (!cedula && !codigo) return;

    // Validación de solo números en cédula (Seguridad extra)
    if (cedula && !/^\d+$/.test(cedula)) {
        mostrarToast("⚠️ La cédula debe contener solo números", "error");
        inputCedula.focus();
        return;
    }
    // Expresión regular: ^B significa que inicia con B, \d+ significa uno o más números después
    if (codigo && !/^B\d+$/.test(codigo)) {
        mostrarToast("⚠️ El código debe iniciar con 'B' seguido de números (Ej: B045)", "error");
        inputCodigo.focus();
        return; 
    }
    const param = cedula ? `nro_cedula=${cedula}` : `codigo=${codigo}`;

    try {
        const data = await apiFetch(`/conductores/buscar?${param}`);
        
        if (data && data.length > 0) {
            seleccionarConductor(data[0]);
            mostrarToast(`✅ Localizado: ${data[0].nombre}`, 'success');
            document.getElementById('conNombre').focus();
        } else {
            // No borramos la búsqueda para que pueda completar el registro
            mostrarToast("ℹ️ Registro no encontrado. Complete los datos para guardar.", 'info');
            resetearFormConductor(false); 
        }
    } catch (err) {
        console.error("Error en búsqueda:", err);
        mostrarToast("📍 Error al consultar servidor", 'error');
    }
}

// 4. GUARDAR O ACTUALIZAR
async function guardarConductor(e) {
    if (e) e.preventDefault();
    
    const id = document.getElementById('conId').value;
    const datos = {
        nro_cedula: document.getElementById('conCedula').value.trim(),
        nombre: document.getElementById('conNombre').value.trim(),
        codigo: document.getElementById('conCodigo').value.trim(),
        nro_telefono: document.getElementById('conTelefono').value.trim()
    };

    const metodo = id ? 'PUT' : 'POST';
    const url = id ? `/conductores/${id}` : '/conductores';

    try {
        await apiFetch(url, {
            method: metodo,
            body: JSON.stringify(datos)
        });

        mostrarToast(id ? "✅ Actualizado correctamente" : "✅ Registrado correctamente", 'success');
        resetearFormConductor(true);
        if (typeof cargarConductores === 'function') cargarConductores();

    } catch (err) {
        console.error("Error al guardar:", err.message);
        let msg = err.message;
        if (msg.includes('{')) {
            try { msg = JSON.parse(msg.substring(msg.indexOf('{'))).error; } catch(e){}
        }
        mostrarToast("⚠️ " + msg, 'error');
    }
}

// 5. INICIALIZACIÓN DE EVENTOS (Unificado)
document.addEventListener('DOMContentLoaded', () => {
    const inputCedula = document.getElementById('conCedula');
    const inputCodigo = document.getElementById('conCodigo');
    const form = document.getElementById('formConductor');

    // Filtro en tiempo real: Solo números en cédula
    if (inputCedula) {
        inputCedula.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
    // Dentro del bloque DOMContentLoaded:
    if (inputCodigo) {
        inputCodigo.addEventListener('input', function() {
            let val = this.value.toUpperCase(); // Forzamos mayúscula
            
            // Si no empieza por B, lo forzamos o limpiamos
            if (val.length > 0 && val[0] !== 'B') {
                val = 'B' + val.replace(/\D/g, ''); // Le pone la B al inicio
            } else if (val.length > 1) {
                // A partir del segundo carácter, solo permitimos números
                val = 'B' + val.substring(1).replace(/\D/g, '');
            }
            
            this.value = val;
        });
    }
    // Manejador de Enter Único
    const manejarEnter = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            validarConductor();
        }
    };

    if (inputCedula) inputCedula.addEventListener('keydown', manejarEnter);
    if (inputCodigo) inputCodigo.addEventListener('keydown', manejarEnter);

    if (form) form.addEventListener('submit', guardarConductor);
});