#!/bin/sh

# Generate timestamp for the backup filename
# Format: YYYYMMDD-HHMM (e.g., 20240404-1216)
DATE=$(date +%Y%m%d-%H%M)

# Define the backup filename with path
# The backup will be stored in /backups directory and compressed with gzip
# Format: waterDB_YYYYMMDD-HHMM.sql.gz
FILENAME=/backups/waterDB_$DATE.sql.gz

# Create database backup using mysqldump
# -h: Specify the host (from DB_HOST environment variable)
# -u: Specify the user (from DB_USER environment variable)
# -p: Specify the password (from DB_PASSWORD environment variable)
# The output is piped to gzip for compression
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" | gzip > "$FILENAME"

# Upload the backup to Google Drive using rclone with environment variables
# This approach uses environment variables directly without creating a config file
export RCLONE_DRIVE_CLIENT_ID="${GOOGLE_CLIENT_ID}"
export RCLONE_DRIVE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET}"
export RCLONE_DRIVE_TOKEN='{"access_token":"'"${GOOGLE_ACCESS_TOKEN}"'","token_type":"Bearer","refresh_token":"'"${GOOGLE_REFRESH_TOKEN}"'","expiry":"2025-04-04T16:28:46.3802263+02:00"}'

# Use rclone with the drive remote configured via environment variables
rclone --config /dev/null copy "$FILENAME" :drive:water-backups

# Clean up old local backups
# This command finds and deletes backup files older than 7 days
# -type f: Only match files
# -mtime +7: Files modified more than 7 days ago
# -name "*.gz": Only match files ending in .gz
find /backups -type f -mtime +7 -name "*.gz" -delete
