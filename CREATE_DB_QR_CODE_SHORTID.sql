-- Crear la base de datos waterplus_short_id (si no existe)
CREATE DATABASE IF NOT EXISTS waterplus_short_id;

-- Usar la base de datos waterplus_short_id
USE waterplus_short_id;

-- Crear la tabla qr_codes (si no existe)
CREATE TABLE IF NOT EXISTS qr_codes (
    short_id VARCHAR(10) PRIMARY KEY UNIQUE,
    value DECIMAL(10, 2),
    state VARCHAR(45),
    creation_date DATE,
    used_date DATETIME
);

select * from qr_codes where short_id="HBeajrUr";
