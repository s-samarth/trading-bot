#!/bin/bash

# Exit on error
set -e

# Configuration
INSTALL_DIR="/opt/trading-bot"
BACKUP_DIR="/opt/trading-bot/backups"
USER="trading"
GROUP="trading"
RETENTION_DAYS=7

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR
chown $USER:$GROUP $BACKUP_DIR

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="trading_bot_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Stop the trading bot service
print_status "Stopping trading bot service"
systemctl stop trading-bot

# Create backup
print_status "Creating backup"
tar -czf "$BACKUP_PATH.tar.gz" \
    -C $INSTALL_DIR \
    config \
    data \
    TradingStrategy \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude="*.log"

# Set proper permissions
chown $USER:$GROUP "$BACKUP_PATH.tar.gz"
chmod 600 "$BACKUP_PATH.tar.gz"

# Clean up old backups
print_status "Cleaning up old backups"
find $BACKUP_DIR -name "trading_bot_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

# Restart the trading bot service
print_status "Restarting trading bot service"
systemctl start trading-bot

# Check service status
if systemctl is-active --quiet trading-bot; then
    print_status "Trading bot service is running"
else
    print_error "Failed to start trading bot service"
    journalctl -u trading-bot -n 50
    exit 1
fi

print_status "Backup completed successfully!"
print_status "Backup location: $BACKUP_PATH.tar.gz"
print_status "Backups are retained for $RETENTION_DAYS days" 