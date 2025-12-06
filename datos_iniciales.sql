-- =========================
-- ROLES
-- =========================
INSERT INTO roles (nombre_rol, descripcion)
VALUES 
('admin', 'Administrador del sistema'),
('operador', 'Operador de despacho');

-- =========================
-- USUARIOS
-- =========================
INSERT INTO usuarios (usuario, clave_hash, nombre_completo, rol_id, activo)
VALUES
('admin1', 'hash_admin', 'Administrador General', 1, 1),
('operador1', 'hash_operador', 'Operador Principal', 2, 1);

-- =========================
-- CLIENTES
-- =========================
INSERT INTO clientes (nro_telefono, nombre, direccion)
VALUES
('04141234567', 'Carlos Pérez', 'Av. Libertador, San Cristóbal'),
('04149876543', 'María Gómez', 'Calle 5, Barrio Obrero');

-- =========================
-- CONDUCTORES
-- =========================
INSERT INTO conductores (cod_conductor, nro_telefono, nombre)
VALUES
('COND001', '04141230001', 'José Ramírez'),
('COND002', '04141230002', 'Luis Fernández');

-- =========================
-- AUTOS
-- =========================
INSERT INTO autos (nro_placa, tipo_auto, marca, modelo)
VALUES
('ABC123', 'Sedán', 'Toyota', 'Corolla'),
('XYZ789', 'Camioneta', 'Chevrolet', 'Trailblazer');

-- =========================
-- TURNOS
-- =========================
INSERT INTO turnos (id_conductores, id_autos, fecha_hora_inicio, estado_turno)
VALUES
(1, 1, datetime('now'), 'activo'),
(2, 2, datetime('now'), 'activo');

-- =========================
-- DISPONIBILIDAD
-- =========================
INSERT INTO disponibilidad (id_conductores, estado, ubicacion, observacion)
VALUES
(1, 'disponible', 'Terminal de pasajeros', 'Listo para servicio'),
(2, 'ocupado', 'Centro', 'En ruta');

-- =========================
-- TARIFAS
-- =========================
INSERT INTO tarifas (tarifa)
VALUES
(5.0),
(7.5),
(10.0);

-- =========================
-- DESPACHOS
-- =========================
INSERT INTO despacho (fecha_hora_inicio, origen_despacho, destino_despacho, cliente_id, conductor_id, auto_id, tarifa, estado_despacho)
VALUES
(datetime('now'), 'Plaza Bolívar', 'Hospital Central', 1, 1, 1, 5.0, 'en curso'),
(datetime('now'), 'Barrio Obrero', 'Terminal de pasajeros', 2, 2, 2, 7.5, 'en curso');
