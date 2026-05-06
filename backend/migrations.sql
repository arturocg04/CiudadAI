-- Script de Migraciones para PostgreSQL
-- Propósito: crear las tablas necesarias para la aplicación CiudadAI
-- Ejecutar: psql -U postgres -d ciudadai < migrations.sql

-- Tabla de Trabajadores
CREATE TABLE IF NOT EXISTS workers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    telefono VARCHAR(9),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workers_email ON workers(email);
CREATE INDEX idx_workers_active ON workers(active);

-- Tabla de Incidencias/Reportes Ciudadanos
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    nif VARCHAR(9) NOT NULL,
    telefono VARCHAR(9) NOT NULL,
    email VARCHAR(255) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    urgencia INTEGER NOT NULL CHECK (urgencia >= 1 AND urgencia <= 5),
    fecha TIMESTAMP NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'nuevo' CHECK (estado IN ('nuevo', 'pendiente', 'cerrado')),
    canal VARCHAR(50),
    direccion_persona VARCHAR(255),
    ubicacion_incid VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para queries comunes
CREATE INDEX idx_incidents_urgencia ON incidents(urgencia);
CREATE INDEX idx_incidents_fecha ON incidents(fecha DESC);
CREATE INDEX idx_incidents_estado ON incidents(estado);
CREATE INDEX idx_incidents_nif ON incidents(nif);
CREATE INDEX idx_incidents_urgencia_fecha ON incidents(urgencia DESC, fecha DESC);

-- Insertar trabajadores de ejemplo
INSERT INTO workers (email, nombre, apellidos, hashed_password, telefono, active)
VALUES 
    ('worker@ciudadai.com', 'Juan', 'García López', '$2b$12$d.YXcDhGBWBEzBKNvgWyJu4XKMYMaNfvVTU.qjAjfVZDrQzgwJDRC', '666777888', TRUE),
    ('admin@ciudadai.com', 'María', 'López Martínez', '$2b$12$r/X7Tiv0X.CpLmvVLDhQtu1MKLkTHfQ1rCJfVNJvpHQXvBKjvKZf.', '666777889', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Ver datos de ejemplo
-- SELECT * FROM workers;
-- SELECT * FROM incidents ORDER BY urgencia DESC, fecha DESC;
