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

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON waterDB.* TO 'gilo'@'%';
FLUSH PRIVILEGES; 