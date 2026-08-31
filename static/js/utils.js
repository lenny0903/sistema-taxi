/// utils.js - Motor Core de Utilidades y Comunicación API

const BASE_URL = window.location.origin.includes('127.0.0.1') || window.location.origin.includes('localhost')
  ? "http://127.0.0.1:5000"
  : ""; // Permite rutas relativas en producción o locales según el entorno

const DEBUG_MODE = true;

// 1. Logger Centralizado
function log(mensaje, tipo = 'info') {
    if (!DEBUG_MODE) return;
    if (tipo === 'error') console.error("❌ " + mensaje);
    else if (tipo === 'success') console.log("✅ " + mensaje);
    else console.log("🔹 " + mensaje);
}

// 2. Cliente HTTP Centralizado con Manejo Inteligente de Errores y Auth
async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...options.headers
  };

  // Ajusta la URL si viene con barra o relativa
  const urlFinal = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

  try {
    const res = await fetch(urlFinal, { ...options, headers });

    // Manejo de Expiración de Sesión
    if (res.status === 401) {
      console.warn("⚠️ Sesión expirada o no autorizada. Redirigiendo a login...");
      localStorage.removeItem("token");
      window.location.href = "/index.html";
      throw new Error("Token expirado o inválido");
    }

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(errorText || `Error ${res.status}`);
    }

    // Devuelve el JSON parseado directamente
    return await res.json();
  } catch (err) {
    console.error(`❌ Error en ${endpoint}:`, err);
    throw err;
  }
}

// Globalizamos apiFetch
window.apiFetch = apiFetch;

// 3. Validadores Sanitizados
function validarNombre(nombre) {
  return nombre && nombre.trim().length >= 2;
}

// 4. Fetch Defensivo para Colecciones o Respuestas Variables
async function fetchDefensivo(url, options = {}) {
  try {
    const data = await apiFetch(url, options);

    if (!data) return [];
    if (data.error) {
      console.error("❌ Error devuelto en JSON:", data.error);
      return [];
    }

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

// 5. Refresco de Estado de Conductores para Despachos
window.refrescarConductoresDisponibles = async function() {
    try {
        const data = await apiFetch("/conductores/en_turno_disponibles");
        window.conductoresGlobales = data; 
        
        if (typeof actualizarContadorConductores === 'function') {
            actualizarContadorConductores(data.length);
        }

        log(`Listado de conductores actualizado (${data.length} disponibles)`, 'success');
        return data;
    } catch (error) {
        console.error("Error al refrescar conductores:", error);
        return [];
    }
};

// 6. Diagnóstico Clínico / Técnico de Conductor
function consultarDiagnosticoWeb(codigoConductor) {
    if (!codigoConductor) {
        if (typeof mostrarToast === 'function') mostrarToast("⚠️ Ingresa un código de conductor.", "error");
        return;
    }

    const url = `/conductores/diagnostico-texto/${encodeURIComponent(codigoConductor.trim())}`;

    apiFetch(url)
        .then(textoReporte => {
            const contenedor = document.getElementById('resultadoDiagnostico');
            if (contenedor) {
                contenedor.innerText = typeof textoReporte === 'string' ? textoReporte : JSON.stringify(textoReporte, null, 2);
                contenedor.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error al consultar diagnóstico:', error);
        });
}

// 7. Inicializador de Eventos Rápidos UI
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById('buscadorRapido')?.addEventListener('input', function() {
        const destinoBusqueda = this.value;
        const resultadoDiv = document.getElementById('resultadoPrecioRapido');
        
        if (!resultadoDiv || typeof MATRIZ_TARIFAS === 'undefined') return;

        const tarifa = MATRIZ_TARIFAS.find(t => t.destino.toLowerCase() === destinoBusqueda.toLowerCase());
        
        if (tarifa) {
            const precioFormateado = new Intl.NumberFormat('es-CO').format(tarifa.precio_cop);
            resultadoDiv.innerText = `$ ${precioFormateado}`;
            resultadoDiv.classList.replace('bg-light', 'bg-warning-subtle');
        } else {
            resultadoDiv.innerText = "$ 0";
            resultadoDiv.classList.replace('bg-warning-subtle', 'bg-light');
        }
    });
});
function toggleMenu() {
    const menu = document.getElementById("menuLateral");
    if (!menu) return;

    // Alternamos clases de ancho o visibilidad
    if (menu.classList.contains("w-64")) {
        menu.classList.remove("w-64");
        menu.classList.add("w-0", "p-0", "opacity-0"); // Oculta el menú por completo o colapsa su ancho
    } else {
        menu.classList.remove("w-0", "p-0", "opacity-0");
        menu.classList.add("w-64");
    }
}