# 🚖 Sistema de Despacho de Taxis

Gestión integral de clientes, turnos, conductores y lista de espera para oficinas de taxis.  
Este sistema asegura que ningún cliente se pierda y que los despachos se realicen de forma ordenada y confiable.

---

## ✨ Funcionalidades principales
- **Validación de clientes**: evita duplicados y despachos múltiples en curso.
- **Gestión de turnos activos**: bloquea la creación de despachos si no hay turnos disponibles.
- **Lista de espera dinámica**: clientes sin conductor quedan registrados y se actualizan automáticamente.
- **Formulario protegido**: solo se habilita si hay conductores libres.
- **Tabla sincronizada**: refleja en tiempo real los cambios al pasar clientes al formulario.
- **Feedback visual**: mensajes claros y estados para operadores.

---

## 🛠️ Tecnologías utilizadas
- **Backend**: Python + Flask
- **Frontend**: HTML, CSS, JavaScript
- **Base de datos**: PostgreSQL / MySQL (según configuración)
- **Entorno**: Linux Mint Debian Edition (LMDE 6/7)

---

## 🚀 Instalación
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/lenny0903/sistema-taxi.git
   cd sistema-taxi
