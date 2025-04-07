#!/bin/sh

# Set error handling
set -e

# Load environment variables
source /scripts/load-env.sh

# Create backups directory if it doesn't exist
mkdir -p /backups

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M)

# Create backup filename using the database name from environment variable
BACKUP_FILE="${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Starting backup process at $(date)"

# Create the backup
echo "Creating MySQL backup..."
mysqldump -h "${DB_HOST}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" | gzip > "/backups/${BACKUP_FILE}"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup created successfully: ${BACKUP_FILE}"
    
    # Upload to Google Drive
    echo "Uploading to Google Drive..."
    rclone copy "/backups/${BACKUP_FILE}" remote:backups/
    
    if [ $? -eq 0 ]; then
        echo "Upload to Google Drive successful"
        
        # Clean up old backups (keep last 7 days)
        echo "Cleaning up old backups..."
        ls -t /backups/${DB_NAME}_*.sql.gz | tail -n +8 | xargs -r rm
        
        echo "Backup process completed successfully at $(date)"
    else
        echo "Error: Failed to upload to Google Drive"
        exit 1
    fi
else
    echo "Error: Failed to create backup"
    exit 1
fi
