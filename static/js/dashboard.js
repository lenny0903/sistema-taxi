document.addEventListener("keydown", function(e) {
    switch(e.key) {
        case "F1":
            e.preventDefault();
            mostrarSeccion("despachos"); // abre el formulario
            mostrarToast("Formulario de Despachos abierto con F1 📝", "info");
            break;

        case "F2":
            e.preventDefault();
            mostrarSeccion("despachosActivos"); // abre despachos activos + lista de espera
            mostrarToast("Despachos Activos y Lista de Espera abiertos con F2 🚕", "info");
            break;

        case "F3":
            e.preventDefault();
            mostrarSeccion("conductores");
            mostrarToast("Gestión de Conductores abierta con F3 👨‍✈️", "info");
            break;

        case "F4":
            e.preventDefault();
            mostrarSeccion("autos");
            mostrarToast("Gestión de Autos abierta con F4 🚗", "info");
            break;

        case "F5":
            e.preventDefault();
            mostrarSeccion("clientesEditar");
            mostrarToast("Gestión de Clientes abierta con F5 👥", "info");
            break;

        case "F6":
            e.preventDefault();
            mostrarSeccion("reportes");
            mostrarToast("Reportes abiertos con F6 📊", "info");
            break;

        case "F7":
            e.preventDefault();
            mostrarSeccion("turnosActivos"); // abre la nueva vista de turnos
            cargarConductoresDisponibles();  // pobla el select de conductores
            cargarAutosDisponiblesSelect();  // pobla el select de autos
            mostrarToast("Gestión de Turnos Activos abierta con F7 ⏱️", "info");
            break;
    }
});
