# QR Code Generator API

API for generating and managing QR codes for vending machines.

## Hardware Specifications

### ESP32-CAM Module
The QR code reader is implemented using an ESP32-CAM module with the following specifications:
- Chip: ESP32-D0WDQ6 (revision v1.0)
- Features: WiFi, BT, Dual Core, 240MHz, VRef calibration in efuse
- Crystal: 40MHz
- Camera: OV2640 camera module
- Flash: 4MB

This module is used in the `qrcode_reader_esp32` component for capturing and processing QR codes.

### Setup Environment

1. Create a virtual environment (recommended):
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- On Windows:
```bash
.venv\Scripts\activate
```
- On Linux/Mac:
```bash
source .venv/bin/activate
```

3. Install MPRemote:
```bash
pip install mpremote
```

### Uploading and Running Files
To work with the ESP32 using MicroPython, you can use the following commands:

1. Upload files to ESP32 flash memory:
```bash
mpremote cp blink_led.py :
```

2. Run a program on the ESP32:
```bash
mpremote run blink_led.py
```

3. List files on the ESP32 Flash:
```bash
mpremote run blink_led.py
```

Note: Always ensure your virtual environment is activated before running MPRemote commands. You can verify this by checking if your terminal prompt starts with `(.venv)`.

If you can't use `mpremote` directly, you can use:
```bash
python -m mpremote cp blink_led.py :
python -m mpremote run blink_led.py
```
```

## Prerequisites

- Docker
- Docker Compose

## Running with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd qr_for_vending
```

2. Create a `.env` file from the example and configure your environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your specific configuration values.

3. Build and start the containers:
```bash
docker-compose up --build
```

The API will be available at http://localhost:3000

## API Documentation

Once the server is running, you can access:
- Swagger UI: http://localhost:3000/docs
- ReDoc: http://localhost:3000/redoc

## API Endpoints

- POST `/api/qrdata` - Create a new QR code
- GET `/api/qrdata/{qrcode_id}` - Get QR code information
- GET `/api/qrcodes` - List all QR codes (with pagination)
- PUT `/api/qrdata/exchange/{qrcode_id}` - Exchange a QR code

## Development

To run the application in development mode:

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the database:
```bash
mysql -u <your_user> -p < create_database_schema.sql
```

4. Run the application:
```bash
python qrcode_generator.py
```

## Environment Variables

The following environment variables must be configured in your `.env` file:

### API Configuration
- `API_URL` - API base URL
- `API_HOST` - API host address
- `API_PORT` - API port number
- `DEBUG` - Debug mode flag

### Database Configuration
- `DB_HOST` - Database host address
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name

### QR Code Configuration
- `QR_MIN_VALUE` - Minimum QR code value
- `QR_SHORT_ID_LENGTH` - Length of QR code ID

### Security Configuration
- `CORS_ORIGINS` - Allowed CORS origins
- `RATE_LIMIT` - API rate limit
- `RATE_LIMIT_PERIOD` - Rate limit period in minutes

### Logging Configuration
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

See `.env.example` for the structure of the environment variables file. 