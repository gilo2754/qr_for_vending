# QR Code Generator API

API for generating and managing QR codes for vending machines.

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