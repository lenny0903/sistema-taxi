async function guardarTodo(id) {
    console.log("🚀 Intentando guardar ID:", id);

    // Capturamos los datos desde los IDs que pusiste en el HTML
    const destino = document.getElementById(`input_destino_${id}`).value;
    const municipio = document.getElementById(`input_municipio_${id}`).value;
    const precio = document.getElementById(`input_tarifa_${id}`).value;

    const datos = {
        id: id,
        destino: destino,
        municipio: municipio,
        precio_cop: precio
    };

    try {
        // 🚩 IMPORTANTE: Cambia la URL a '/actualizar_tarifa' para que coincida con tu Python
        const res = await fetch('/actualizar_tarifa', { 
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(datos)
        });

        const resultado = await res.json();

        if (res.ok && resultado.status === "success") {
            alert(`✅ Sector ${destino} actualizado correctamente.`);
            console.log("Respuesta del servidor:", resultado);
            
            // Si usas Socket.io para avisar al operador:
            if (typeof socket !== 'undefined') {
                socket.emit('matriz_actualizada', datos);
            }
        } else {
            console.error("❌ Error del servidor:", resultado.message);
        }
    } catch (error) {
        console.error("❌ Error en la comunicación:", error);
    }
}

// Escuchador de Socket.io para cambios remotos
socket.on('matriz_actualizada', function() {
    console.log("🔄 Sincronizando cambios desde el servidor...");
    // Aquí podrías recargar la tabla o solo avisar
    // location.reload(); // Opción rápida pero ruda
});