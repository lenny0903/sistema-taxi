/// utils.js

const BASE_URL = "http://127.0.0.1:5000";

async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...options.headers
  };

  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });

    // --- MANEJO INTELIGENTE DEL ERROR 401 ---
    if (res.status === 401) {
      console.warn("⚠️ Sesión expirada. Redirigiendo a login...");
      window.location.href = '/login';
      throw new Error("Token expirado");
    }

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Error ${res.status}: ${text}`);
    }

    return await res.json();
  } catch (err) {
    console.error(`❌ Error en ${endpoint}:`, err);
    throw err;
  }
}

// Hacemos que sea global para usarla en todo tu sistema
window.apiFetch = apiFetch;


function validarNombre(nombre) {
  return nombre && nombre.trim().length >= 2;
}

// ==================== Fetch defensivo ====================
async function fetchDefensivo(url, options = {}) {
  try {
    const data = await apiFetch(url, options);

    if (!data) return [];

    if (data.error) {
      console.error("❌ Error en respuesta:", data.error);
      return [];
    }

    console.log("📡 Datos recibidos:", data);

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

window.refrescarConductoresDisponibles = async function() {
    try {
        const data = await apiFetch("/conductores/en_turno_disponibles");
        window.conductoresGlobales = data; 
        
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
    
    const tarifa = MATRIZ_TARIFAS.find(t => t.destino === destinoBusqueda);
    
    if (tarifa) {
        const precioFormateado = new Intl.NumberFormat('es-CO').format(tarifa.precio_cop);
        resultadoDiv.innerText = `$ ${precioFormateado}`;
        resultadoDiv.classList.replace('bg-light', 'bg-warning-subtle');
    } else {
        resultadoDiv.innerText = "$ 0";
        resultadoDiv.classList.replace('bg-warning-subtle', 'bg-light');
    }
});

const DEBUG_MODE = true; 

function log(mensaje, tipo = 'info') {
    if (!DEBUG_MODE) return;
    
    if (tipo === 'error') console.error("❌ " + mensaje);
    else if (tipo === 'success') console.log("✅ " + mensaje);
    else console.log("🔹 " + mensaje);
}

log("Dashboard sincronizado", 'success');

// 🟢 Función para colapsar/expandir el menú lateral
function toggleMenu() {
    const menu = document.getElementById('menuLateral');
    if (menu.style.width === '0px' || menu.classList.contains('w-0')) {
        menu.classList.remove('w-0', 'p-0', 'opacity-0');
        menu.classList.add('w-64', 'p-3');
        menu.style.width = '';
    } else {
        menu.classList.remove('w-64', 'p-3');
        menu.classList.add('w-0', 'p-0', 'opacity-0');
        menu.style.width = '0px';
    }
}