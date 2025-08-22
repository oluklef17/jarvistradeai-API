#!/bin/bash

# Database Migration Script for Jarvistrade Production
# This script handles database migrations safely

set -e  # Exit on any error

# Configuration
COMPOSE_FILE="docker-compose.yml"
LOG_FILE="./logs/migrate.log"
BACKUP_BEFORE_MIGRATION=true

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
mkdir -p "$(dirname "$LOG_FILE")"

log "Starting database migration process..."

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

# Check if services are running
if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    error "Services are not running. Please start them first with 'docker-compose up -d'"
    exit 1
fi

# Check if PostgreSQL is healthy
if ! docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "healthy"; then
    error "PostgreSQL is not healthy. Please check the service status."
    exit 1
fi

# Check if the app container is running
if ! docker-compose -f "$COMPOSE_FILE" ps app | grep -q "Up"; then
    error "Application container is not running. Please start it first."
    exit 1
fi

# Create backup before migration if enabled
if [[ "$BACKUP_BEFORE_MIGRATION" == "true" ]]; then
    log "Creating database backup before migration..."
    
    BACKUP_DIR="./backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/pre_migration_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U jarvistrade_user \
        -d jarvistrade_prod \
        --clean \
        --if-exists \
        --create \
        --verbose \
        > "$BACKUP_FILE"; then
        
        log "Pre-migration backup created: $BACKUP_FILE"
    else
        warning "Failed to create pre-migration backup"
    fi
fi

# Check current migration status
log "Checking current migration status..."
if docker-compose -f "$COMPOSE_FILE" exec -T app alembic current; then
    log "Current migration status retrieved"
else
    error "Failed to get current migration status"
    exit 1
fi

# Show available migrations
log "Available migrations:"
if docker-compose -f "$COMPOSE_FILE" exec -T app alembic history --verbose; then
    log "Migration history retrieved"
else
    error "Failed to get migration history"
    exit 1
fi

# Check for pending migrations
log "Checking for pending migrations..."
PENDING_MIGRATIONS=$(docker-compose -f "$COMPOSE_FILE" exec -T app alembic check 2>&1 || true)

if [[ -n "$PENDING_MIGRATIONS" ]]; then
    log "Pending migrations found:"
    echo "$PENDING_MIGRATIONS"
else
    log "No pending migrations found"
fi

# Ask for confirmation before proceeding
echo
read -p "Do you want to proceed with the migration? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Migration cancelled by user"
    exit 0
fi

# Run the migration
log "Starting database migration..."
if docker-compose -f "$COMPOSE_FILE" exec -T app alembic upgrade head; then
    log "Database migration completed successfully!"
else
    error "Database migration failed!"
    
    # Show recent logs for debugging
    log "Recent application logs:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50 app
    
    # Show migration status
    log "Current migration status:"
    docker-compose -f "$COMPOSE_FILE" exec -T app alembic current || true
    
    exit 1
fi

# Verify migration
log "Verifying migration..."
if docker-compose -f "$COMPOSE_FILE" exec -T app alembic current; then
    log "Migration verification successful"
else
    error "Migration verification failed"
    exit 1
fi

# Check database health
log "Checking database health..."
if docker-compose -f "$COMPOSE_FILE" exec -T app python -c "
from database import check_database_health
if check_database_health():
    print('Database health check passed')
    exit(0)
else:
    print('Database health check failed')
    exit(1)
"; then
    log "Database health check passed"
else
    error "Database health check failed"
    exit 1
fi

# Test application endpoints
log "Testing application endpoints..."
HEALTH_ENDPOINTS=("/health" "/health/detailed")

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    if curl -f "http://localhost:8000$endpoint" > /dev/null 2>&1; then
        log "✓ $endpoint is healthy"
    else
        warning "✗ $endpoint health check failed"
    fi
done

# Show final migration status
log "Final migration status:"
docker-compose -f "$COMPOSE_FILE" exec -T app alembic current

log "Database migration completed successfully!"
log "The application is ready to use with the new schema."

# Optional: Restart application if needed
read -p "Do you want to restart the application to ensure all changes are loaded? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Restarting application..."
    docker-compose -f "$COMPOSE_FILE" restart app
    log "Application restarted"
fi

