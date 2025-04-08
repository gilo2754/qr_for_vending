-- Use the database (already created by MySQL)
USE waterDB;

-- Create the qr_codes table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS qr_codes (
    qrcode_id VARCHAR(10) PRIMARY KEY UNIQUE,
    value DECIMAL(10, 2),
    state VARCHAR(45),
    creation_date DATE,
    used_date DATETIME,
    qr_image MEDIUMBLOB
);

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert test records to verify the table exists
-- QR de prueba - Estado: válido
INSERT INTO qr_codes (qrcode_id, value, state, creation_date) 
VALUES ('TEST_VALIDO', 10.00, 'valido', CURDATE());

-- QR de prueba - Estado: enCirculación
INSERT INTO qr_codes (qrcode_id, value, state, creation_date) 
VALUES ('TEST_CIRCUL', 15.00, 'enCirculacion', CURDATE());

-- QR de prueba - Estado: usado
INSERT INTO qr_codes (qrcode_id, value, state, creation_date, used_date) 
VALUES ('TEST_USADO', 5.00, 'usado', DATE_SUB(CURDATE(), INTERVAL 2 DAY), NOW());

-- QR de prueba - Estado: expirado
INSERT INTO qr_codes (qrcode_id, value, state, creation_date) 
VALUES ('TEST_EXPIR', 20.00, 'expirado', DATE_SUB(CURDATE(), INTERVAL 30 DAY));

-- QR de prueba - Estado: invalidado
INSERT INTO qr_codes (qrcode_id, value, state, creation_date) 
VALUES ('TEST_INVAL', 25.00, 'invalidado', DATE_SUB(CURDATE(), INTERVAL 5 DAY));

-- Insert test users
INSERT INTO users (username, password_hash, email, full_name, role) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vYBxLri', 'admin@example.com', 'Administrador', 'admin');

INSERT INTO users (username, password_hash, email, full_name, role) 
VALUES ('user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vYBxLri', 'user@example.com', 'Usuario Normal', 'user');

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON waterDB.* TO 'gilo'@'%';
FLUSH PRIVILEGES; 