let bloqueoGuardar = false;
let buscandoPlaca = false; // 🛡️ Bandera para el Enter de búsqueda
function seleccionarAuto(auto) {
    console.log("Auto seleccionado desde tabla:", auto);
    
    // Llenamos los campos del formulario
    document.getElementById('autoId').value = auto.id_auto;
    document.getElementById('autoPlaca').value = auto.nro_placa;
    document.getElementById('autoTipo').value = auto.tipo_auto;
    document.getElementById('autoMarca').value = auto.marca;
    document.getElementById('autoModelo').value = auto.modelo;

    // Cambiamos el botón a modo edición
    const btn = document.getElementById('btnGuardarAuto');
    if (btn) {
        btn.textContent = "Actualizar Cambios";
        btn.classList.remove('bg-green-500');
        btn.classList.add('bg-blue-600');
    }
}
/**
 * Busca un vehículo por placa
 */
async function validarAuto() {
    const placaInput = document.getElementById('autoPlaca');
    const placa = placaInput.value.trim().toUpperCase(); // Normalizamos a mayúsculas
    if (!placa) return;

    try {
        console.log("🚀 Buscando auto por placa:", placa);
        const data = await apiFetch(`/autos/buscar?placa=${placa}`);
        
        const btn = document.getElementById('btnGuardarAuto');

        if (data && data.length > 0) {
            const a = data[0];
            console.log("🔍 Datos recibidos de Python:", a);

            // 1. ASIGNAR ID (Probamos todas las variantes posibles de nombre)
            const idReal = a.id_auto || a.id;
            const inputId = document.getElementById('autoId');
            
            if (inputId && idReal) {
                inputId.value = idReal;
                console.log("✅ ID guardado en el input hidden:", inputId.value);
            } else {
                console.error("❌ Error: No se encontró el input 'autoId' o el objeto no trae ID");
            }
            
            // 2. RELLENAR CAMPOS (Asegúrate de que los IDs coincidan con tu HTML)
            document.getElementById('autoPlaca').value = a.nro_placa;
            document.getElementById('autoTipo').value = a.tipo_auto || "";
            document.getElementById('autoMarca').value = a.marca || "";
            document.getElementById('autoModelo').value = a.modelo || "";
            
            // 3. CAMBIAR INTERFAZ A MODO EDICIÓN
            if (btn) {
                btn.textContent = "Actualizar Cambios";
                // Usamos remove y add para asegurar el cambio de color
                btn.classList.remove('bg-green-500');
                btn.classList.add('bg-blue-600');
            }
            
            // Corregido: usamos nro_placa que es el nombre real en tu modelo
            mostrarToast(`Auto ${a.nro_placa} cargado para edición`, 'success');

        } else {
            console.warn("ℹ️ Placa nueva detectada.");
            
            // 4. MODO REGISTRO NUEVO
            document.getElementById('autoId').value = ""; // ID vacío = POST
            if (btn) {
                btn.textContent = "Guardar Nuevo";
                btn.classList.remove('bg-blue-600');
                btn.classList.add('bg-green-500');
            }
            mostrarToast("Placa no registrada. Complete los datos.", 'info');
        }
    } catch (err) {
        console.error("❌ Error en la validación:", err.message);
        mostrarToast("Error al buscar: " + err.message, 'error');
    }
}
// autos.js
async function guardarAuto(e) {
    
    if (e) e.preventDefault();

    // 🛡️ BLOQUEO ESTRICTO ANTI-DOBLE DISPARO
    if (bloqueoGuardar) return;
    bloqueoGuardar = true;

    const boton = document.getElementById('btnGuardarAuto');
    if (boton.disabled) {
        bloqueoGuardar = false;
        return;
    }
    
    // BLOQUEO DE SEGURIDAD: Si el botón ya está desactivado, no hagas nada
    if (boton.disabled) return; 

    const autoId = document.getElementById('autoId').value;
    const placaIngresada = document.getElementById('autoPlaca').value.trim().toUpperCase();

   // 🛡️ VALIDACIÓN: Formato BXY (B y dos números) DEBE ESTAR AL FINAL.
    // La expresión regular busca "B" + 2 dígitos justo antes del final de la cadena.
    const regexPlacaFinal = /B\d{2}$/;
   if (!regexPlacaFinal.test(placaIngresada)) {
        validandoPlaca = true;
        alert("Formato inválido. La placa debe terminar con la letra B seguida de dos números (Ej: ABC-B07).");
        document.getElementById('autoPlaca').focus();
        validandoPlaca = false; // Liberamos la bandera al cerrar
        return;
    }
    const datos = {
        nro_placa: placaIngresada,
        tipo_auto: document.getElementById('autoTipo').value,
        marca: document.getElementById('autoMarca').value,
        modelo: document.getElementById('autoModelo').value
    };

    // Desactivamos el botón INMEDIATAMENTE
    boton.disabled = true;
    const textoOriginal = boton.innerHTML;
    boton.innerHTML = "Enviando...";

    try {
        const metodo = autoId ? 'PUT' : 'POST';
        const url = autoId ? `/autos/${autoId}` : '/autos/';

        const response = await fetch(url, {
            method: metodo,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });

        const resData = await response.json();

        if (response.ok) {
            alert("¡Vehículo guardado con éxito!");
            document.getElementById('formAuto').reset();
            document.getElementById('autoId').value = "";
            if (typeof cargarAutosTabla === 'function') await cargarAutosTabla();
        } else {
            // Si el servidor dice que ya existe (Error 400), lo mostramos bonito
            Swal.fire("Aviso", resData.error || "Error", "warning");
        }
    } catch (error) {
        console.error("Error:", error);
    } finally {
        // Solo reactivamos el botón después de que todo termine
        boton.disabled = false;
        boton.innerHTML = textoOriginal;
    }
}
function resetearFormAuto(limpiarPlaca = true) {
    // Si limpiarPlaca es true, borra la placa. Si es false (cuando no se encuentra), la deja.
    if (limpiarPlaca) {
        document.getElementById('autoPlaca').value = "";
    }
    
    // Limpiamos el ID oculto y los demás campos
    document.getElementById('autoId').value = "";
    document.getElementById('autoTipo').value = "";
    document.getElementById('autoMarca').value = "";
    document.getElementById('autoModelo').value = "";
    
    // Restauramos el botón a su estado original (Verde / Guardar)
    const btn = document.getElementById('btnGuardarAuto');
    if (btn) {
        btn.textContent = "Guardar";
        btn.classList.remove('bg-blue-600');
        btn.classList.add('bg-green-500');
    }
    console.log("Formulario de autos reseteado.");
}
// Escuchador de Tecla Enter para Autos
document.addEventListener('keydown', function(e) {
    // Verificamos que sea el Enter Y que estemos en el campo autoPlaca
    if (e.key === 'Enter' && e.target.id === 'autoPlaca') {
        e.preventDefault();

        // 🛡️ BLOQUEO: Si ya se está procesando una búsqueda, ignoramos este doble evento
        if (buscandoPlaca) return;
        buscandoPlaca = true;

        console.log("Enter detectado en autoPlaca");
        
        validarAuto().finally(() => {
            // Liberamos el bloqueo medio segundo después para permitir buscar de nuevo
            setTimeout(() => {
                buscandoPlaca = false;
            }, 500);
        });
    }
});
// Agrega esto a autos.js para que el clic en la tabla funcione

// Mantén tus funciones guardarAuto y resetearFormAuto igual...
document.addEventListener('DOMContentLoaded', () => {
    const formAuto = document.getElementById('formAuto');
    if (formAuto) {
        formAuto.onsubmit = guardarAuto; // Conecta el envío del formulario
    }
});