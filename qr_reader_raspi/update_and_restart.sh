#!/bin/bash

# Log file for the update process
LOG_FILE="/var/log/qr_reader_update.log"

# Directory where the repository is located
REPO_DIR="/home/camenjiv/Desktop/qr_for_vending"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Navigate to repository directory
cd "$REPO_DIR" || {
    log_message "Error: Could not change to repository directory"
    exit 1
}

# Log start of update
log_message "Starting update process..."

# Fetch and pull latest changes
log_message "Pulling latest changes..."
git fetch origin
git reset --hard origin/main

# Check if qrcode_reader_raspi.py is running and stop it
PID=$(pgrep -f "python.*qrcode_reader_raspi.py")
if [ ! -z "$PID" ]; then
    log_message "Stopping existing QR reader process (PID: $PID)..."
    kill "$PID"
    sleep 2
fi

# Start the QR reader script in the background
log_message "Starting QR reader script..."
cd "$REPO_DIR" && nohup python automa_raspi/qrcode_reader_raspi.py > /dev/null 2>&1 &

# Log completion
log_message "Update process completed successfully" 