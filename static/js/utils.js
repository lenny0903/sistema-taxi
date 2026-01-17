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