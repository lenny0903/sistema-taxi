window.onload = cargarUsuarios;
async function cargarUsuarios() {
      console.log("Entrando a cargarUsuarios()");
      try {
        const res = await fetch("/usuarios/usuarios"); // ruta correcta
        if (!res.ok) throw new Error("Error HTTP " + res.status);

        const usuarios = await res.json();
        const tbody = document.querySelector("#tablaUsuarios tbody");
        tbody.innerHTML = "";
        console.log("Usuarios recibidos:", usuarios);

        usuarios.forEach(u => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${u.id_usuario}</td>
            <td>${u.usuario}</td>
            <td>${u.nombre_completo}</td>
            <td>${u.nombre_rol}</td>
            <td>${u.activo ? "Sí" : "No"}</td>
            <td>
              <button class="btn btn-sm btn-warning" onclick="toggleUsuario(${u.id_usuario}, ${u.activo})">
                ${u.activo ? "Desactivar" : "Activar"}
              </button>
            </td>
          `;
          tbody.appendChild(tr);
        });
      } catch (err) {
        console.error("Error cargando usuarios:", err);
        alert("No se pudo cargar la lista de usuarios");
      }
    }