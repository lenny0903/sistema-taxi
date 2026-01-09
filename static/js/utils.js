async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      "Authorization": "Bearer " + localStorage.getItem("token")
    }
  });

  if (!res.ok) throw new Error("HTTP " + res.status);
  return await res.json(); // 👈 siempre JSON
}


function validarNombre(nombre) {
  return nombre && nombre.trim().length >= 2;
}
async function fetchDefensivo(url, options = {}) {
  try {
    let data = await apiFetch(url, options);

    // 🚨 Si por error llega un Response crudo
    if (data instanceof Response) {
      console.warn("⚠️ apiFetch devolvió Response en vez de JSON, corrigiendo...");
      data = await data.json();
    }

    console.log("📡 Datos recibidos:", data);

    // Normalizar formatos
    if (Array.isArray(data)) {
      return data;
    } else if (data && typeof data === "object") {
      if (data.cliente) return [data.cliente];
      if (data.clientes) return data.clientes;
      if (data.despachos) return data.despachos;
      return [data]; // objeto plano
    } else {
      return [];
    }
  } catch (err) {
    console.error("❌ Error en fetchDefensivo:", err);
    return [];
  }
}
