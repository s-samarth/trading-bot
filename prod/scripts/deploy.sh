#!/bin/bash

# Exit on error
set -e

# Configuration
INSTALL_DIR="/opt/trading-bot"
USER="trading"
GROUP="trading"
PYTHON_VERSION="3.9"
VENV_DIR="$INSTALL_DIR/venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

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

# Create system user and group if they don't exist
if ! getent group $GROUP >/dev/null; then
    print_status "Creating group $GROUP"
    groupadd $GROUP
fi

if ! getent passwd $USER >/dev/null; then
    print_status "Creating user $USER"
    useradd -m -g $GROUP -s /bin/bash $USER
fi

# Create installation directory
print_status "Creating installation directory"
mkdir -p $INSTALL_DIR
chown $USER:$GROUP $INSTALL_DIR

# Install system dependencies
print_status "Installing system dependencies"
apt-get update
apt-get install -y \
    python$PYTHON_VERSION \
    python$PYTHON_VERSION-venv \
    python$PYTHON_VERSION-dev \
    build-essential \
    git

# Create and activate virtual environment
print_status "Setting up Python virtual environment"
python$PYTHON_VERSION -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

# Create necessary directories
print_status "Creating application directories"
mkdir -p $INSTALL_DIR/{config,data,logs}
chown -R $USER:$GROUP $INSTALL_DIR

# Copy application files
print_status "Copying application files"
cp -r "$PROJECT_ROOT/TradingStrategy" $INSTALL_DIR/
cp "$SCRIPT_DIR/../services/trading-bot.service" /etc/systemd/system/
cp "$SCRIPT_DIR/../config/prod_config.json" $INSTALL_DIR/config/

# Set proper permissions
print_status "Setting file permissions"
chown -R $USER:$GROUP $INSTALL_DIR
chmod 600 $INSTALL_DIR/config/prod_config.json
chmod 755 $INSTALL_DIR/TradingStrategy

# Create log directory
print_status "Setting up logging"
mkdir -p /var/log/trading-bot
chown $USER:$GROUP /var/log/trading-bot

# Reload systemd and enable service
print_status "Configuring systemd service"
systemctl daemon-reload
systemctl enable trading-bot
systemctl start trading-bot

# Check service status
print_status "Checking service status"
if systemctl is-active --quiet trading-bot; then
    print_status "Trading bot service is running"
else
    print_error "Failed to start trading bot service"
    journalctl -u trading-bot -n 50
    exit 1
fi

print_status "Deployment completed successfully!"
print_warning "Please edit $INSTALL_DIR/config/prod_config.json with your settings"
print_status "You can check the service status with: systemctl status trading-bot"
print_status "View logs with: journalctl -u trading-bot -f" 