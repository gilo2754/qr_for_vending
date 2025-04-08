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

-- Insert a test record to verify the table exists
INSERT INTO qr_codes (qrcode_id, value, state, creation_date) 
VALUES ('TEST123', 10.00, 'active', CURDATE());

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON waterDB.* TO 'gilo'@'%';
FLUSH PRIVILEGES; 