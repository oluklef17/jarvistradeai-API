#!/bin/bash

# Backup Script for Jarvistrade Production
# This script handles automated backups of database and files

set -e  # Exit on any error

# Configuration
BACKUP_DIR="./backups"
LOG_FILE="./logs/backup.log"
RETENTION_DAYS=30
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Create necessary directories
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log "Starting backup process..."

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check if .env file exists
if [[ ! -f .env ]]; then
    error ".env file not found. Please create one based on env.example"
    exit 1
fi

# Load environment variables
source .env

# Generate timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_PATH"

log "Creating backup: $BACKUP_NAME"

# Database backup
log "Creating database backup..."
if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
    DB_BACKUP_FILE="$BACKUP_PATH/database.sql"
    
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U jarvistrade_user \
        -d jarvistrade_prod \
        --clean \
        --if-exists \
        --create \
        --verbose \
        > "$DB_BACKUP_FILE"; then
        
        log "Database backup created successfully: $(du -h "$DB_BACKUP_FILE" | cut -f1)"
    else
        error "Database backup failed"
        exit 1
    fi
else
    warning "PostgreSQL container is not running, skipping database backup"
fi

# File backups
log "Creating file backups..."

# Uploads directory
if [[ -d "./uploads" ]]; then
    log "Backing up uploads directory..."
    tar -czf "$BACKUP_PATH/uploads.tar.gz" -C . uploads/
    log "Uploads backup created: $(du -h "$BACKUP_PATH/uploads.tar.gz" | cut -f1)"
fi

# Digital products directory
if [[ -d "./digital_products" ]]; then
    log "Backing up digital products directory..."
    tar -czf "$BACKUP_PATH/digital_products.tar.gz" -C . digital_products/
    log "Digital products backup created: $(du -h "$BACKUP_PATH/digital_products.tar.gz" | cut -f1)"
fi

# Licenses directory
if [[ -d "./licenses" ]]; then
    log "Backing up licenses directory..."
    tar -czf "$BACKUP_PATH/licenses.tar.gz" -C . licenses/
    log "Licenses backup created: $(du -h "$BACKUP_PATH/licenses.tar.gz" | cut -f1)"
fi

# Logs directory (compressed)
if [[ -d "./logs" ]]; then
    log "Backing up logs directory..."
    tar -czf "$BACKUP_PATH/logs.tar.gz" -C . logs/
    log "Logs backup created: $(du -h "$BACKUP_PATH/logs.tar.gz" | cut -f1)"
fi

# Environment and configuration files
log "Backing up configuration files..."
cp .env "$BACKUP_PATH/" 2>/dev/null || warning "Could not backup .env file"
cp docker-compose.yml "$BACKUP_PATH/" 2>/dev/null || warning "Could not backup docker-compose.yml"
cp requirements.txt "$BACKUP_PATH/" 2>/dev/null || warning "Could not backup requirements.txt"

# Create backup manifest
log "Creating backup manifest..."
cat > "$BACKUP_PATH/manifest.txt" << EOF
Backup created: $(date)
Backup name: $BACKUP_NAME
Environment: ${ENVIRONMENT:-production}

Contents:
- Database: $(ls -la "$BACKUP_PATH"/database.sql 2>/dev/null | awk '{print $5}' || echo "Not available")
- Uploads: $(ls -la "$BACKUP_PATH"/uploads.tar.gz 2>/dev/null | awk '{print $5}' || echo "Not available")
- Digital Products: $(ls -la "$BACKUP_PATH"/digital_products.tar.gz 2>/dev/null | awk '{print $5}' || echo "Not available")
- Licenses: $(ls -la "$BACKUP_PATH"/licenses.tar.gz 2>/dev/null | awk '{print $5}' || echo "Not available")
- Logs: $(ls -la "$BACKUP_PATH"/logs.tar.gz 2>/dev/null | awk '{print $5}' || echo "Not available")

Total backup size: $(du -sh "$BACKUP_PATH" | cut -f1)
EOF

# Create compressed archive of entire backup
log "Creating compressed backup archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
cd - > /dev/null

# Remove uncompressed backup directory
rm -rf "$BACKUP_PATH"

# Calculate final backup size
FINAL_BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
log "Backup archive created: ${BACKUP_NAME}.tar.gz ($FINAL_BACKUP_SIZE)"

# Cleanup old backups
log "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

# Show backup summary
log "Backup completed successfully!"
log "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
log "Backup size: $FINAL_BACKUP_SIZE"

# List all backups
log "Available backups:"
ls -lah "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null || log "No backups found"

# Optional: Upload to cloud storage (uncomment and configure as needed)
# log "Uploading backup to cloud storage..."
# aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" "s3://your-bucket/backups/" || warning "Cloud upload failed"

log "Backup process completed!"

