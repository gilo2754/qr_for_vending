# QR Code Generator API

API for generating and managing QR codes for vending machines.

## Prerequisites

- Docker
- Docker Compose
- Google Drive account (for backups)

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

## Automatic Backups

The application includes an automatic backup system that:
- Creates daily database backups at 3 AM
- Compresses backups using gzip
- Uploads backups to Google Drive
- Maintains a 7-day retention policy
- Stores backups in both local storage and Google Drive

### Backup Configuration

The backup system is configured in the `docker-compose.yml` file and uses:
- A dedicated backup container (`mysql-backup`)
- Cron for scheduling
- Rclone for Google Drive integration

### Backup Files

Backups are stored in:
- Local: `./backups/` directory
- Google Drive: In the configured folder

Backup files follow the naming convention: `waterDB_YYYYMMDD-HHMM.sql.gz`

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
mysql -u <your_user> -p < 01-create-database.sql
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

### Backup Configuration
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GOOGLE_ACCESS_TOKEN` - Google OAuth access token
- `GOOGLE_REFRESH_TOKEN` - Google OAuth refresh token

See `.env.example` for the structure of the environment variables file.

## ESP32 Integration

For ESP32-CAM setup and usage instructions, please refer to [ESP32_README.md](ESP32_README.md). 