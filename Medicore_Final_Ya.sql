-- =========================================================
-- MEDICORE - BASE DE DATOS
-- Orden del script:
--   1. Crear la base de datos
--   2. Crear las tablas
--   3. Datos de prueba
--   4. Verificación
-- =========================================================


-- =========================================================
-- 1. CREAR LA BASE DE DATOS
-- =========================================================

CREATE DATABASE IF NOT EXISTS MediCore;
USE MediCore;


-- =========================================================
-- 2. TABLAS
-- =========================================================

-- 2.1 Especialidades médicas
CREATE TABLE Especialidades_Medicas (
    ID_Especialidad INT AUTO_INCREMENT PRIMARY KEY,
    Nombre_Especialidad VARCHAR(100) NOT NULL UNIQUE
);

-- 2.2 Médicos
CREATE TABLE Medicos (
    ID_Medico INT AUTO_INCREMENT PRIMARY KEY,
    Codigo_MINSA VARCHAR(20) NOT NULL UNIQUE,
    Nombre VARCHAR(100) NOT NULL,
    ID_Especialidad INT NOT NULL,
    Turno ENUM('Matutino','Vespertino','Nocturno') NOT NULL,

    FOREIGN KEY (ID_Especialidad)
        REFERENCES Especialidades_Medicas(ID_Especialidad)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 2.3 Pacientes
-- Cedula puede ser NULL (los menores de edad no tienen cédula).
CREATE TABLE Pacientes (
    ID_Paciente INT AUTO_INCREMENT PRIMARY KEY,
    Cedula VARCHAR(16) NULL UNIQUE,
    Nombre VARCHAR(100) NOT NULL,
    Fecha_Nacimiento DATE NOT NULL,
    Sexo ENUM('Masculino','Femenino') NULL,
    Tipo_Sangre ENUM(
        'A+','A-','B+','B-',
        'AB+','AB-','O+','O-'
    ) NOT NULL,
    Alergias TEXT
);

-- 2.4 Agenda de horarios
CREATE TABLE Agenda_Horarios (
    ID_Agenda INT AUTO_INCREMENT PRIMARY KEY,
    ID_Medico INT NOT NULL,
    Dia_Semana ENUM(
        'Lunes','Martes','Miercoles',
        'Jueves','Viernes','Sabado','Domingo'
    ) NOT NULL,
    Hora_Inicio TIME NOT NULL,
    Hora_Fin TIME NOT NULL,
    -- 1 = horario especial (fuera del turno del médico)
    Horario_Especial TINYINT NOT NULL DEFAULT 0,

    CHECK (Hora_Inicio < Hora_Fin),

    FOREIGN KEY (ID_Medico)
        REFERENCES Medicos(ID_Medico)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- 2.5 Citas médicas
CREATE TABLE Citas_Medicas (
    ID_Cita INT AUTO_INCREMENT PRIMARY KEY,
    ID_Paciente INT NOT NULL,
    ID_Medico INT NOT NULL,
    Fecha DATE NOT NULL,
    Hora TIME NOT NULL,
    Estado ENUM(
        'Programada',
        'Asistio',
        'Cancelada'
    ) DEFAULT 'Programada',

    FOREIGN KEY (ID_Paciente)
        REFERENCES Pacientes(ID_Paciente)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (ID_Medico)
        REFERENCES Medicos(ID_Medico)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 2.6 Expedientes clínicos
-- Lugar_Expediente: ubicación física (formato A-001), única por expediente.
CREATE TABLE Expedientes_Clinicos (
    ID_Expediente INT AUTO_INCREMENT PRIMARY KEY,
    ID_Paciente INT NOT NULL UNIQUE,
    Fecha_Creacion DATE NOT NULL DEFAULT (CURRENT_DATE),
    Lugar_Expediente VARCHAR(5) NULL UNIQUE,

    FOREIGN KEY (ID_Paciente)
        REFERENCES Pacientes(ID_Paciente)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 2.7 Consultas e historial
CREATE TABLE Consultas_Historial (
    ID_Consulta INT AUTO_INCREMENT PRIMARY KEY,
    ID_Expediente INT NOT NULL,
    ID_Medico INT NOT NULL,
    ID_Cita INT NOT NULL UNIQUE,
    Fecha_Consulta DATE NOT NULL,
    Presion_Arterial VARCHAR(10) NOT NULL,
    Peso DECIMAL(5,2) NOT NULL,
    Sintomas TEXT NOT NULL,
    Diagnostico TEXT NOT NULL,

    CHECK (Peso > 0),

    FOREIGN KEY (ID_Expediente)
        REFERENCES Expedientes_Clinicos(ID_Expediente)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (ID_Medico)
        REFERENCES Medicos(ID_Medico)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (ID_Cita)
        REFERENCES Citas_Medicas(ID_Cita)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 2.8 Recetas médicas
CREATE TABLE Recetas_Medicas (
    ID_Receta INT AUTO_INCREMENT PRIMARY KEY,
    ID_Consulta INT NOT NULL UNIQUE,
    Fecha_Emision DATE NOT NULL DEFAULT (CURRENT_DATE),

    FOREIGN KEY (ID_Consulta)
        REFERENCES Consultas_Historial(ID_Consulta)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 2.9 Catálogo de medicamentos
CREATE TABLE Medicamentos_Catalogo (
    ID_Medicamento INT AUTO_INCREMENT PRIMARY KEY,
    Nombre_Medicamento VARCHAR(100) NOT NULL UNIQUE,
    Presentacion VARCHAR(100) NOT NULL,
    Existencia INT NOT NULL DEFAULT 0,

    CHECK (Existencia >= 0)
);

-- 2.10 Detalle de receta
CREATE TABLE Detalle_Receta (
    ID_Receta INT NOT NULL,
    ID_Medicamento INT NOT NULL,
    Dosis_Indicada VARCHAR(100) NOT NULL,
    Frecuencia VARCHAR(100) NOT NULL,
    Duracion VARCHAR(100) NOT NULL,
    Cantidad INT NOT NULL DEFAULT 1,

    CHECK (Cantidad > 0),

    PRIMARY KEY (ID_Receta, ID_Medicamento),

    FOREIGN KEY (ID_Receta)
        REFERENCES Recetas_Medicas(ID_Receta)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (ID_Medicamento)
        REFERENCES Medicamentos_Catalogo(ID_Medicamento)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 2.11 Usuarios del sistema
CREATE TABLE Usuarios (
    ID_Usuario INT AUTO_INCREMENT PRIMARY KEY,
    Nombre_Usuario VARCHAR(50) NOT NULL UNIQUE,
    Contrasena_Hash VARCHAR(255) NOT NULL,
    Nombre_Completo VARCHAR(120) NOT NULL,

    Rol ENUM(
        'Administrador',
        'Administrativo',
        'Medico'
    ) NOT NULL,

    ID_Medico INT NULL,

    Estado ENUM(
        'Activo',
        'Inactivo'
    ) NOT NULL DEFAULT 'Activo',

    CONSTRAINT fk_usuarios_medicos
        FOREIGN KEY (ID_Medico)
        REFERENCES Medicos(ID_Medico)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_usuario_medico
        UNIQUE (ID_Medico)
);


-- =========================================================
-- 3. DATOS DE PRUEBA
-- Se insertan en orden de dependencia (primero las tablas
-- de las que dependen las demás).
-- =========================================================

-- 3.1 Especialidades médicas
INSERT INTO Especialidades_Medicas (Nombre_Especialidad)
SELECT v.nombre
FROM (
    SELECT 'Medicina General' AS nombre
    UNION ALL SELECT 'Pediatria'
    UNION ALL SELECT 'Cardiologia'
    UNION ALL SELECT 'Ginecologia'
    UNION ALL SELECT 'Dermatologia'
) v
WHERE NOT EXISTS (
    SELECT 1
    FROM Especialidades_Medicas e
    WHERE e.Nombre_Especialidad = v.nombre
);

-- 3.2 Médicos
INSERT INTO Medicos (Codigo_MINSA, Nombre, ID_Especialidad, Turno)
SELECT v.codigo, v.nombre, e.ID_Especialidad, v.turno
FROM (
    SELECT
        'MINSA-0001' AS codigo,
        'Carlos Gabriel Mendoza Velazquez' AS nombre,
        'Medicina General' AS especialidad,
        'Matutino' AS turno

    UNION ALL SELECT 'MINSA-0002', 'Ana Julia Rodriguez Flores',          'Pediatria',    'Vespertino'
    UNION ALL SELECT 'MINSA-0003', 'Alejandro José Ramírez Torres',       'Cardiologia',  'Matutino'
    UNION ALL SELECT 'MINSA-0004', 'Isabella Sofía Martínez López',       'Ginecologia',  'Nocturno'
    UNION ALL SELECT 'MINSA-0005', 'Sebastián Daniel González Rivera',    'Dermatologia', 'Vespertino'
) v
JOIN Especialidades_Medicas e
    ON e.Nombre_Especialidad = v.especialidad
WHERE NOT EXISTS (
    SELECT 1
    FROM Medicos m
    WHERE m.Codigo_MINSA = v.codigo
);

-- 3.3 Pacientes
-- Sofia (menor de edad) no tiene cédula: se guarda como NULL.
-- En el resto del script los pacientes se identifican por su nombre.
INSERT INTO Pacientes (
    Cedula,
    Nombre,
    Fecha_Nacimiento,
    Sexo,
    Tipo_Sangre,
    Alergias
)
SELECT
    v.cedula,
    v.nombre,
    v.nacimiento,
    v.sexo,
    v.sangre,
    v.alergias
FROM (
    SELECT
        '281-120598-1006F' AS cedula,
        'Maria Luisa Lopez Altamirano' AS nombre,
        '1998-05-12' AS nacimiento,
        'Femenino' AS sexo,
        'O+' AS sangre,
        'Ninguna' AS alergias

    UNION ALL SELECT '281-200805-1014H', 'Juan Bosco Perez Gonzales',        '2005-08-20', 'Masculino', 'A+',  'Penicilina'
    UNION ALL SELECT NULL,               'Sofia Elizabeth Garcia Zamora',    '2015-03-15', 'Femenino',  'B+',  'Ninguna'
    UNION ALL SELECT '281-021175-1213A', 'Pedro Josue Ramirez Correa',       '1975-11-02', 'Masculino', 'AB+', 'Polvo y polen'
    UNION ALL SELECT '281-270289-1019G', 'Lucia Rebeca Martinez Cerda',      '1989-02-27', 'Femenino',  'O-',  'Ninguna'
) v
WHERE NOT EXISTS (
    SELECT 1
    FROM Pacientes p
    WHERE p.Nombre = v.nombre
);

-- 3.4 Agenda de horarios
INSERT INTO Agenda_Horarios (
    ID_Medico,
    Dia_Semana,
    Hora_Inicio,
    Hora_Fin
)
SELECT m.ID_Medico, v.dia, v.ini, v.fin
FROM (
    SELECT
        'MINSA-0001' AS codigo,
        'Lunes' AS dia,
        '08:00:00' AS ini,
        '12:00:00' AS fin

    UNION ALL SELECT 'MINSA-0002', 'Martes',    '14:00:00', '18:00:00'
    UNION ALL SELECT 'MINSA-0003', 'Jueves',    '08:00:00', '12:00:00'
    UNION ALL SELECT 'MINSA-0004', 'Viernes',   '20:00:00', '23:00:00'
    UNION ALL SELECT 'MINSA-0005', 'Miercoles', '14:00:00', '18:00:00'
) v
JOIN Medicos m
    ON m.Codigo_MINSA = v.codigo
WHERE NOT EXISTS (
    SELECT 1
    FROM Agenda_Horarios a
    WHERE a.ID_Medico = m.ID_Medico
      AND a.Dia_Semana = v.dia
      AND a.Hora_Inicio = v.ini
);

-- 3.5 Citas médicas
INSERT INTO Citas_Medicas (
    ID_Paciente,
    ID_Medico,
    Fecha,
    Hora,
    Estado
)
SELECT
    p.ID_Paciente,
    m.ID_Medico,
    v.fecha,
    v.hora,
    v.estado
FROM (
    SELECT
        'Maria Luisa Lopez Altamirano' AS paciente,
        'MINSA-0001' AS codigo,
        '2026-11-02' AS fecha,
        '08:30:00' AS hora,
        'Programada' AS estado

    UNION ALL SELECT 'Maria Luisa Lopez Altamirano', 'MINSA-0001', '2026-10-12', '08:30:00', 'Asistio'
    UNION ALL SELECT 'Juan Bosco Perez Gonzales', 'MINSA-0001', '2026-10-19', '09:00:00', 'Asistio'
    UNION ALL SELECT 'Sofia Elizabeth Garcia Zamora', 'MINSA-0002', '2026-10-20', '15:00:00', 'Asistio'
    UNION ALL SELECT 'Pedro Josue Ramirez Correa', 'MINSA-0003', '2026-10-22', '09:30:00', 'Asistio'
    UNION ALL SELECT 'Lucia Rebeca Martinez Cerda', 'MINSA-0005', '2026-10-21', '15:00:00', 'Asistio'
) v
JOIN Pacientes p
    ON p.Nombre = v.paciente
JOIN Medicos m
    ON m.Codigo_MINSA = v.codigo
WHERE NOT EXISTS (
    SELECT 1
    FROM Citas_Medicas c
    WHERE c.ID_Paciente = p.ID_Paciente
      AND c.ID_Medico = m.ID_Medico
      AND c.Fecha = v.fecha
      AND c.Hora = v.hora
);

-- 3.6 Expedientes clínicos
INSERT INTO Expedientes_Clinicos (
    ID_Paciente,
    Fecha_Creacion,
    Lugar_Expediente
)
SELECT p.ID_Paciente, v.creacion, v.lugar
FROM (
    SELECT
        'Maria Luisa Lopez Altamirano' AS paciente,
        '2026-09-15' AS creacion,
        'A-001' AS lugar

    UNION ALL SELECT 'Juan Bosco Perez Gonzales', '2026-09-16', 'A-002'
    UNION ALL SELECT 'Sofia Elizabeth Garcia Zamora', '2026-09-17', 'A-003'
    UNION ALL SELECT 'Pedro Josue Ramirez Correa', '2026-09-18', 'A-004'
    UNION ALL SELECT 'Lucia Rebeca Martinez Cerda', '2026-09-21', 'A-005'
) v
JOIN Pacientes p
    ON p.Nombre = v.paciente
WHERE NOT EXISTS (
    SELECT 1
    FROM Expedientes_Clinicos e
    WHERE e.ID_Paciente = p.ID_Paciente
);

-- 3.7 Consultas del historial
INSERT INTO Consultas_Historial (
    ID_Expediente,
    ID_Medico,
    ID_Cita,
    Fecha_Consulta,
    Presion_Arterial,
    Peso,
    Sintomas,
    Diagnostico
)
SELECT
    e.ID_Expediente,
    m.ID_Medico,
    c.ID_Cita,
    c.Fecha,
    v.presion,
    v.peso,
    v.sintomas,
    v.diagnostico
FROM (
    SELECT
        'Maria Luisa Lopez Altamirano' AS paciente,
        'MINSA-0001' AS codigo,
        '2026-10-12' AS fecha,
        '08:30:00' AS hora,
        '118/76' AS presion,
        62.50 AS peso,
        'Dolor de garganta, malestar general y fiebre leve desde hace dos dias.' AS sintomas,
        'Faringitis aguda.' AS diagnostico

    UNION ALL SELECT
        'Juan Bosco Perez Gonzales', 'MINSA-0001', '2026-10-19', '09:00:00',
        '125/82', 74.30,
        'Dolor de cabeza frecuente y congestion nasal durante una semana.',
        'Rinitis alergica con cefalea tensional.'

    UNION ALL SELECT
        'Sofia Elizabeth Garcia Zamora', 'MINSA-0002', '2026-10-20', '15:00:00',
        '100/65', 38.20,
        'Fiebre y tos seca durante tres dias, sin dificultad para respirar.',
        'Infeccion respiratoria viral.'

    UNION ALL SELECT
        'Pedro Josue Ramirez Correa', 'MINSA-0003', '2026-10-22', '09:30:00',
        '148/94', 86.40,
        'Dolor de cabeza en las mananas y mareos ocasionales.',
        'Hipertension arterial leve.'

    UNION ALL SELECT
        'Lucia Rebeca Martinez Cerda', 'MINSA-0005', '2026-10-21', '15:00:00',
        '110/70', 58.90,
        'Picazon y enrojecimiento en los antebrazos desde hace dos semanas.',
        'Dermatitis de contacto.'
) v
JOIN Pacientes p
    ON p.Nombre = v.paciente
JOIN Medicos m
    ON m.Codigo_MINSA = v.codigo
JOIN Expedientes_Clinicos e
    ON e.ID_Paciente = p.ID_Paciente
JOIN Citas_Medicas c
    ON c.ID_Paciente = p.ID_Paciente
   AND c.ID_Medico = m.ID_Medico
   AND c.Fecha = v.fecha
   AND c.Hora = v.hora
WHERE NOT EXISTS (
    SELECT 1
    FROM Consultas_Historial h
    WHERE h.ID_Cita = c.ID_Cita
);

-- 3.8 Recetas médicas
INSERT INTO Recetas_Medicas (
    ID_Consulta,
    Fecha_Emision
)
SELECT h.ID_Consulta, h.Fecha_Consulta
FROM (
    SELECT 'Maria Luisa Lopez Altamirano' AS paciente, '2026-10-12' AS fecha
    UNION ALL SELECT 'Juan Bosco Perez Gonzales', '2026-10-19'
    UNION ALL SELECT 'Sofia Elizabeth Garcia Zamora', '2026-10-20'
    UNION ALL SELECT 'Pedro Josue Ramirez Correa', '2026-10-22'
    UNION ALL SELECT 'Lucia Rebeca Martinez Cerda', '2026-10-21'
) v
JOIN Pacientes p
    ON p.Nombre = v.paciente
JOIN Citas_Medicas c
    ON c.ID_Paciente = p.ID_Paciente
   AND c.Fecha = v.fecha
JOIN Consultas_Historial h
    ON h.ID_Cita = c.ID_Cita
WHERE NOT EXISTS (
    SELECT 1
    FROM Recetas_Medicas r
    WHERE r.ID_Consulta = h.ID_Consulta
);

-- 3.9 Catálogo de medicamentos
INSERT INTO Medicamentos_Catalogo (
    Nombre_Medicamento,
    Presentacion,
    Existencia
)
SELECT v.nombre, v.presentacion, v.existencia
FROM (
    SELECT
        'Acetaminofen' AS nombre,
        'Tabletas 500 mg' AS presentacion,
        250 AS existencia

    UNION ALL SELECT 'Amoxicilina', 'Capsulas 500 mg', 120
    UNION ALL SELECT 'Loratadina',  'Tabletas 10 mg',  140
    UNION ALL SELECT 'Losartan',    'Tabletas 50 mg',  5
    UNION ALL SELECT 'Omeprazol',   'Capsulas 20 mg',  95
) v
WHERE NOT EXISTS (
    SELECT 1
    FROM Medicamentos_Catalogo mc
    WHERE mc.Nombre_Medicamento = v.nombre
);

-- 3.10 Detalle de recetas
INSERT INTO Detalle_Receta (
    ID_Receta,
    ID_Medicamento,
    Dosis_Indicada,
    Frecuencia,
    Duracion
)
SELECT
    r.ID_Receta,
    md.ID_Medicamento,
    v.dosis,
    v.frecuencia,
    v.duracion
FROM (
    SELECT
        'Maria Luisa Lopez Altamirano' AS paciente,
        '2026-10-12' AS fecha,
        'Amoxicilina' AS medicamento,
        '1 capsula (500 mg)' AS dosis,
        'Cada 8 horas' AS frecuencia,
        '7 dias' AS duracion

    UNION ALL SELECT
        'Juan Bosco Perez Gonzales', '2026-10-19', 'Loratadina',
        '1 tableta (10 mg)', 'Cada 24 horas', '5 dias'

    UNION ALL SELECT
        'Sofia Elizabeth Garcia Zamora', '2026-10-20', 'Acetaminofen',
        '1 tableta (500 mg)', 'Cada 8 horas si hay fiebre', '3 dias'

    UNION ALL SELECT
        'Pedro Josue Ramirez Correa', '2026-10-22', 'Losartan',
        '1 tableta (50 mg)', 'Cada 24 horas', '30 dias'

    UNION ALL SELECT
        'Lucia Rebeca Martinez Cerda', '2026-10-21', 'Loratadina',
        '1 tableta (10 mg)', 'Cada 24 horas', '7 dias'
) v
JOIN Pacientes p
    ON p.Nombre = v.paciente
JOIN Citas_Medicas c
    ON c.ID_Paciente = p.ID_Paciente
   AND c.Fecha = v.fecha
JOIN Consultas_Historial h
    ON h.ID_Cita = c.ID_Cita
JOIN Recetas_Medicas r
    ON r.ID_Consulta = h.ID_Consulta
JOIN Medicamentos_Catalogo md
    ON md.Nombre_Medicamento = v.medicamento
WHERE NOT EXISTS (
    SELECT 1
    FROM Detalle_Receta d
    WHERE d.ID_Receta = r.ID_Receta
      AND d.ID_Medicamento = md.ID_Medicamento
);

-- 3.11 Usuarios de prueba
-- Usuario médico
INSERT INTO Usuarios (
    Nombre_Usuario,
    Contrasena_Hash,
    Nombre_Completo,
    Rol,
    ID_Medico,
    Estado
)
SELECT
    'CarlosM',
    'pbkdf2_sha256$600000$02ce6c43a0e3c96c46bfbdf35574289c$b0a7632cba071ca144cd5d8aa422524751b6e5e182829ee40bd827019817c004',
    'Carlos Gabriel Mendoza Velazquez',
    'Medico',
    m.ID_Medico,
    'Activo'
FROM Medicos m
WHERE m.Codigo_MINSA = 'MINSA-0001'
  AND NOT EXISTS (
      SELECT 1
      FROM Usuarios u
      WHERE u.Nombre_Usuario = 'CarlosM'
  );

-- Usuario administrativo
INSERT INTO Usuarios (
    Nombre_Usuario,
    Contrasena_Hash,
    Nombre_Completo,
    Rol,
    ID_Medico,
    Estado
)
SELECT
    'Secretaria1',
    'pbkdf2_sha256$600000$02ce6c43a0e3c96c46bfbdf35574289c$b0a7632cba071ca144cd5d8aa422524751b6e5e182829ee40bd827019817c004',
    'Usuario Administrativo',
    'Administrativo',
    NULL,
    'Activo'
WHERE NOT EXISTS (
    SELECT 1
    FROM Usuarios u
    WHERE u.Nombre_Usuario = 'Secretaria1'
);


-- =========================================================
-- 4. VERIFICACIÓN: cantidad de filas por tabla
-- =========================================================

SELECT 'Especialidades_Medicas' AS tabla, COUNT(*) AS filas FROM Especialidades_Medicas
UNION ALL SELECT 'Medicos',               COUNT(*) FROM Medicos
UNION ALL SELECT 'Pacientes',             COUNT(*) FROM Pacientes
UNION ALL SELECT 'Agenda_Horarios',       COUNT(*) FROM Agenda_Horarios
UNION ALL SELECT 'Citas_Medicas',         COUNT(*) FROM Citas_Medicas
UNION ALL SELECT 'Expedientes_Clinicos',  COUNT(*) FROM Expedientes_Clinicos
UNION ALL SELECT 'Consultas_Historial',   COUNT(*) FROM Consultas_Historial
UNION ALL SELECT 'Recetas_Medicas',       COUNT(*) FROM Recetas_Medicas
UNION ALL SELECT 'Medicamentos_Catalogo', COUNT(*) FROM Medicamentos_Catalogo
UNION ALL SELECT 'Detalle_Receta',        COUNT(*) FROM Detalle_Receta
UNION ALL SELECT 'Usuarios',              COUNT(*) FROM Usuarios;


-- =========================================================
-- ANEXO: SOLO SI TU BASE DE DATOS YA EXISTÍA
-- (No lo ejecutes en una instalación nueva: las columnas ya
--  vienen incluidas en los CREATE TABLE de arriba.)
-- =========================================================
--
-- ALTER TABLE Pacientes MODIFY Cedula VARCHAR(16) NULL;
--
-- ALTER TABLE Pacientes
--     ADD COLUMN Sexo ENUM('Masculino','Femenino') NULL AFTER Fecha_Nacimiento;
--
-- ALTER TABLE Expedientes_Clinicos
--     ADD COLUMN Lugar_Expediente VARCHAR(5) NULL AFTER Fecha_Creacion,
--     ADD UNIQUE (Lugar_Expediente);
--
-- ALTER TABLE Detalle_Receta
--     ADD COLUMN Cantidad INT NOT NULL DEFAULT 1 AFTER Duracion,
--     ADD CONSTRAINT chk_detalle_cantidad CHECK (Cantidad > 0);
--
-- ALTER TABLE Agenda_Horarios
--     ADD COLUMN Horario_Especial TINYINT NOT NULL DEFAULT 0 AFTER Hora_Fin;
--
-- -- Marca como "especiales" los horarios que ya existían fuera del turno
-- -- (así no se pierde ninguno). Revisa el resultado después.
-- UPDATE Agenda_Horarios a
-- JOIN Medicos m ON m.ID_Medico = a.ID_Medico
-- SET a.Horario_Especial = 1
-- WHERE a.ID_Agenda > 0
--   AND NOT (
--        (m.Turno = 'Matutino'   AND a.Hora_Inicio >= '07:00:00' AND a.Hora_Fin <= '12:00:00')
--     OR (m.Turno = 'Vespertino' AND a.Hora_Inicio >= '12:00:00' AND a.Hora_Fin <= '20:00:00')
--     OR (m.Turno = 'Nocturno'   AND (a.Hora_Fin <= '07:00:00' OR a.Hora_Inicio >= '20:00:00'))
--   );