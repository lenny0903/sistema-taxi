// utils.js
async function apiFetch(endpoint, options = {}) {
  // 🔗 URL base del backend centralizada aquí
  const baseUrl = "http://127.0.0.1:5000";

  // 🔑 Token JWT almacenado en localStorage
  const token = localStorage.getItem("token");

  // 📝 Headers comunes + token si existe
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  try {
    // 🚀 Llamada al backend con URL completa y headers
    const res = await fetch(baseUrl + endpoint, { ...options, headers });

    // ⚠️ Manejo de errores HTTP con detalle del backend
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Error ${res.status}: ${text}`);
    }

    // 📡 Devuelve siempre JSON parseado
    return await res.json();
  } catch (err) {
    // ❌ Log de error centralizado
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
    let data = await apiFetch(url, options);

    if (data instanceof Response) {
      console.warn("⚠️ apiFetch devolvió Response en vez de JSON, aplicando fallback .json()");
      data = await data.json();
    }

    if (data.error) {
      console.error("❌ Error en respuesta:", data.error);
      return [];
    }

    console.log("📡 Datos recibidos:", data);

    if (Array.isArray(data)) {
      return data;
    } else if (data && typeof data === "object") {
      if (data.cliente) return [data.cliente];
      if (data.clientes) return data.clientes;
      if (data.despachos) return data.despachos;
      return [data];
    } else {
      return [];
    }
  } catch (err) {
    console.error("❌ Error en fetchDefensivo:", err);
    return [];
  }
}




