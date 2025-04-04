-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS waterDB;

-- Use the database
USE waterDB;

-- Create the qr_codes table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS qr_codes (
    qrcode_id VARCHAR(10) PRIMARY KEY UNIQUE,
    value DECIMAL(10, 2),
    state VARCHAR(45),
    creation_date DATE,
    used_date DATETIME
);

select * from qr_codes where qrcode_id="HBeajrUr";

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON waterDB.* TO 'gilo'@'%';
FLUSH PRIVILEGES;
