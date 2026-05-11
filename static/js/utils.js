// utils.js
async function apiFetch(endpoint, options = {}) {
  const baseUrl = "http://127.0.0.1:5000";
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...options.headers
  };

  try {
    const res = await fetch(baseUrl + endpoint, { ...options, headers });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Error ${res.status}: ${text}`);
    }

    // 🔥 VITAL: Debes retornar el JSON ya resuelto
    return await res.json(); 
  } catch (err) {
    console.error("❌ Error en apiFetch:", err);
    throw err;
  }
}


function validarNombre(nombre) {
  return nombre && nombre.trim().length >= 2;
}
// ==================== Fetch defensivo ====================
async function fetchDefensivo(url, options = {}) {
  try {
    // 1. Confiamos en que apiFetch ya devuelve el JSON parseado
    const data = await apiFetch(url, options);

    // 2. Si apiFetch falló catastróficamente, vendrá null/undefined
    if (!data) return [];

    // 3. Manejo de errores que vienen dentro del JSON
    if (data.error) {
      console.error("❌ Error en respuesta:", data.error);
      return [];
    }

    console.log("📡 Datos recibidos:", data);

    // 4. Mapeo inteligente de datos
    if (Array.isArray(data)) return data;
    
    if (typeof data === "object") {
      if (data.cliente) return [data.cliente];
      if (data.clientes) return data.clientes;
      if (data.despachos) return data.despachos;
      return [data];
    }
    
    return [];
  } catch (err) {
    console.error("❌ Error en fetchDefensivo:", err);
    return [];
  }
}

// Asegura que sea global asignándola a window
window.refrescarConductoresDisponibles = async function() {
    try {
        const data = await apiFetch("/conductores/en_turno_disponibles");
        window.conductoresGlobales = data; 
        
        // Verificación de seguridad para no romper el código
        if (typeof actualizarContadorConductores === 'function') {
            actualizarContadorConductores(data.length);
        }

        console.log("🔄 Lista de conductores actualizada:", data);
        return data;
    } catch (error) {
        console.error("Error al refrescar conductores:", error);
        return [];
    }
};

document.getElementById('buscadorRapido')?.addEventListener('input', function() {
    const destinoBusqueda = this.value;
    const resultadoDiv = document.getElementById('resultadoPrecioRapido');
    
    // Buscamos en la matriz global que ya cargamos desde Flask
    const tarifa = MATRIZ_TARIFAS.find(t => t.destino === destinoBusqueda);
    
    if (tarifa) {
        // Formateamos el número para que se vea profesional (ej: 5.000)
        const precioFormateado = new Intl.NumberFormat('es-CO').format(tarifa.precio_cop);
        resultadoDiv.innerText = `$ ${precioFormateado}`;
        resultadoDiv.classList.replace('bg-light', 'bg-warning-subtle'); // Resalte visual
    } else {
        resultadoDiv.innerText = "$ 0";
        resultadoDiv.classList.replace('bg-warning-subtle', 'bg-light');
    }
});

const DEBUG_MODE = true; // Cámbialo a false antes del estrés o producción

function log(mensaje, tipo = 'info') {
    if (!DEBUG_MODE) return;
    
    if (tipo === 'error') console.error("❌ " + mensaje);
    else if (tipo === 'success') console.log("✅ " + mensaje);
    else console.log("🔹 " + mensaje);
}

// Ejemplo de uso:
log("Dashboard sincronizado", 'success');

window.apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  const baseHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': 'Bearer ' + token } : {})
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers: { ...baseHeaders, ...(options.headers || {}) }
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Error ${res.status}: ${errorText}`);
    }

    // Retornamos el JSON de una vez para simplificar el resto del sistema
    return await res.json(); 
  } catch (err) {
    console.error("❌ Error en apiFetch:", err);
    throw err;
  }
};