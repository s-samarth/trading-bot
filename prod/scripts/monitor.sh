#!/bin/bash

# Exit on error
set -e

# Configuration
INSTALL_DIR="/opt/trading-bot"
LOG_DIR="/var/log/trading-bot"
USER="trading"
GROUP="trading"

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

# Function to check service status
check_service() {
    if systemctl is-active --quiet trading-bot; then
        print_status "Trading bot service is running"
        return 0
    else
        print_error "Trading bot service is not running"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local usage=$(df -h $INSTALL_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 85 ]; then
        print_error "Disk space usage is high: ${usage}%"
        return 1
    else
        print_status "Disk space usage: ${usage}%"
        return 0
    fi
}

# Function to check log file size
check_log_size() {
    local log_file="$LOG_DIR/trading.log"
    if [ -f "$log_file" ]; then
        local size=$(du -h "$log_file" | cut -f1)
        print_status "Log file size: $size"
    else
        print_warning "Log file not found"
    fi
}

# Function to check recent errors
check_recent_errors() {
    local error_count=$(journalctl -u trading-bot -n 100 | grep -i "error" | wc -l)
    if [ "$error_count" -gt 0 ]; then
        print_warning "Found $error_count recent errors in logs"
        echo "Recent errors:"
        journalctl -u trading-bot -n 100 | grep -i "error" | tail -n 5
    else
        print_status "No recent errors found"
    fi
}

# Function to check database integrity
check_database() {
    local db_file="$INSTALL_DIR/data/trading.db"
    if [ -f "$db_file" ]; then
        if sqlite3 "$db_file" "PRAGMA integrity_check;" | grep -q "ok"; then
            print_status "Database integrity check passed"
            return 0
        else
            print_error "Database integrity check failed"
            return 1
        fi
    else
        print_warning "Database file not found"
        return 1
    fi
}

# Function to check system resources
check_resources() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
    local mem_usage=$(free | grep Mem | awk '{print $3/$2 * 100.0}' | cut -d. -f1)

    if [ "$cpu_usage" -gt 80 ]; then
        print_warning "High CPU usage: ${cpu_usage}%"
    else
        print_status "CPU usage: ${cpu_usage}%"
    fi

    if [ "$mem_usage" -gt 80 ]; then
        print_warning "High memory usage: ${mem_usage}%"
    else
        print_status "Memory usage: ${mem_usage}%"
    fi
}

# Main monitoring function
main() {
    echo "=== Trading Bot System Health Check ==="
    echo "Time: $(date)"
    echo "----------------------------------------"

    check_service
    check_disk_space
    check_log_size
    check_recent_errors
    check_database
    check_resources

    echo "----------------------------------------"
    echo "Health check completed"
}

# Run main function
main
