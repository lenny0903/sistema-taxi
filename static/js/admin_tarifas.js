async function guardarTodo(id) {
    // Capturamos los tres campos del DOM
    const inputDestino = document.getElementById(`input_destino_${id}`);
    const inputMunicipio = document.getElementById(`input_municipio_${id}`);
    const inputTarifa = document.getElementById(`input_tarifa_${id}`);

    const datos = {
        id: id,
        destino: inputDestino.value,
        municipio: inputMunicipio.value,
        precio_cop: inputTarifa.value
    };

    try {
        const res = await fetch('/actualizar_matriz_completa', { 
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(datos)
        });

        if (res.ok) {
            // Feedback visual para el usuario en Táchira
            [inputDestino, inputMunicipio, inputTarifa].forEach(el => {
                el.classList.add('is-valid');
                setTimeout(() => el.classList.remove('is-valid'), 2000);
            });
            console.log(`✅ Registro ${id} actualizado con éxito.`);
        }
    } catch (error) {
        console.error("❌ Error en la comunicación con el servidor:", error);
    }
}

// Escuchador de Socket.io para cambios remotos
socket.on('matriz_actualizada', function() {
    console.log("🔄 Sincronizando cambios desde el servidor...");
    // Aquí podrías recargar la tabla o solo avisar
    // location.reload(); // Opción rápida pero ruda
});