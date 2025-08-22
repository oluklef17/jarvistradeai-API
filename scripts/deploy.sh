#!/bin/bash

# Production Deployment Script for Jarvistrade
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy.log"

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
   exit 1
fi

# Create necessary directories
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log "Starting deployment for environment: $ENVIRONMENT"

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
    exit 1
fi

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

# Validate required environment variables
required_vars=("SECRET_KEY" "POSTGRES_PASSWORD" "REDIS_PASSWORD")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        error "Required environment variable $var is not set"
        exit 1
    fi
done

# Backup existing database if it exists
if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
    log "Creating database backup before deployment..."
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U jarvistrade_user jarvistrade_prod > "$BACKUP_FILE"; then
        log "Database backup created: $BACKUP_FILE"
    else
        warning "Failed to create database backup"
    fi
fi

# Stop existing services
log "Stopping existing services..."
docker-compose -f "$COMPOSE_FILE" down

# Pull latest images
log "Pulling latest Docker images..."
docker-compose -f "$COMPOSE_FILE" pull

# Build and start services
log "Building and starting services..."
docker-compose -f "$COMPOSE_FILE" up -d --build

# Wait for services to be healthy
log "Waiting for services to be healthy..."
timeout=300
elapsed=0

while [[ $elapsed -lt $timeout ]]; do
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
        log "All services are healthy"
        break
    fi
    
    sleep 10
    elapsed=$((elapsed + 10))
    
    if [[ $elapsed -eq $timeout ]]; then
        error "Timeout waiting for services to be healthy"
        docker-compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
done

# Run database migrations
log "Running database migrations..."
if docker-compose -f "$COMPOSE_FILE" exec -T app alembic upgrade head; then
    log "Database migrations completed successfully"
else
    error "Database migrations failed"
    docker-compose -f "$COMPOSE_FILE" logs app
    exit 1
fi

# Verify application health
log "Verifying application health..."
sleep 10  # Give the app time to fully start

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log "Application health check passed"
else
    error "Application health check failed"
    docker-compose -f "$COMPOSE_FILE" logs app
    exit 1
fi

# Check all endpoints
log "Running comprehensive health checks..."
HEALTH_ENDPOINTS=("/health" "/health/detailed" "/health/ready" "/health/live")

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    if curl -f "http://localhost:8000$endpoint" > /dev/null 2>&1; then
        log "✓ $endpoint is healthy"
    else
        warning "✗ $endpoint health check failed"
    fi
done

# Cleanup old backups (keep last 10)
log "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +11 | xargs -r rm --
cd - > /dev/null

# Final status check
log "Deployment completed successfully!"
log "Services status:"
docker-compose -f "$COMPOSE_FILE" ps

log "Application is available at:"
log "  - HTTP:  http://localhost (redirects to HTTPS)"
log "  - HTTPS: https://localhost"
log "  - API:   https://localhost/api"
log "  - Health: https://localhost/health"

# Show recent logs
log "Recent application logs:"
docker-compose -f "$COMPOSE_FILE" logs --tail=20 app

log "Deployment script completed successfully!"

