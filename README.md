# QR Code Vending System

System for managing QR codes in vending machines, consisting of two main components:

1. **Generator**: REST API for generating and managing QR codes
2. **Reader**: Application for reading and processing QR codes from a USB scanner

## Project Structure

```
qr_for_vending/
├── qrcodes_generator_api_python.py  # REST API for QR generation
├── qrcode_reader.py                # QR code reader
├── requirements.txt                # Dependencies
```

## Requirements

- Python 3.7+
- MySQL Server
- USB QR code scanner
- Dependencies listed in requirements.txt

## Setup

1. Create a `.env` file in the project root:
```env
# API Configuration
API_URL=http://localhost:3000
API_HOST=0.0.0.0
API_PORT=3000
DEBUG=True

# Database Configuration
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database

# QR Code Configuration
QR_MIN_VALUE=0.05
QR_SHORT_ID_LENGTH=8

# Security Configuration
CORS_ORIGINS=*
RATE_LIMIT=100
RATE_LIMIT_PERIOD=1

# Logging Configuration
LOG_LEVEL=INFO
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the API
```bash
python qrcodes_generator_api_python.py
```

### Start the Reader
```bash
python qrcode_reader.py
```

## API Endpoints

- `POST /api/qrdata`: Create a new QR code
- `GET /api/qrdata/<short_id>`: Get QR code information
- `GET /api/qrcodes`: List all QR codes
- `PUT /api/qrdata/canjear/<short_id>`: Redeem a QR code 