#!/bin/bash

# Create necessary directories
echo "Creating directories..."
mkdir -p backups scripts

# Copy scripts
echo "Copying scripts..."
cp scripts/backup-mysql.sh scripts/
cp scripts/load-env.sh scripts/

# Set correct permissions
echo "Setting permissions..."
chmod +x scripts/backup-mysql.sh
chmod +x scripts/load-env.sh

echo "Setup completed successfully!"
echo "Next steps:"
echo "1. Create your .env file from .env.example"
echo "2. Update the .env file with your actual credentials"
echo "3. Deploy the stack in Portainer" 