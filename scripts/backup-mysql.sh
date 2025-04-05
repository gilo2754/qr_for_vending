#!/bin/sh

# Set error handling
set -e

# Load environment variables
source /scripts/load-env.sh

# Create backups directory if it doesn't exist
mkdir -p /backups

# Generate timestamp for the backup file
TIMESTAMP=$(date +"%Y%m%d-%H%M")
BACKUP_FILE="waterDB_${TIMESTAMP}.sql.gz"
BACKUP_PATH="/backups/${BACKUP_FILE}"

echo "Starting backup process at $(date)"

# Create the backup
echo "Creating MySQL backup..."
mysqldump -h "${DB_HOST}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" | gzip > "${BACKUP_PATH}"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup created successfully: ${BACKUP_FILE}"
    
    # Upload to Google Drive
    echo "Uploading to Google Drive..."
    rclone copy "${BACKUP_PATH}" remote:backups/
    
    if [ $? -eq 0 ]; then
        echo "Upload to Google Drive successful"
        
        # Keep only the latest backup locally
        echo "Cleaning up old local backups..."
        ls -t /backups/waterDB_*.sql.gz | tail -n +2 | xargs -r rm
        
        echo "Backup process completed successfully at $(date)"
    else
        echo "Error: Failed to upload to Google Drive"
        exit 1
    fi
else
    echo "Error: Failed to create backup"
    exit 1
fi
