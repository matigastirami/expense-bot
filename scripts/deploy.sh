#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="expense-tracker-bot"
IMAGE_TAG="latest"
HEALTH_URL="http://localhost:8000/health"
MAX_HEALTH_CHECKS=30

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

check_dependencies() {
    log "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        error "curl is not installed"
        exit 1
    fi
    
    log "All dependencies are available"
}

backup_logs() {
    log "Backing up logs..."
    if [ -d "./logs" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        cp -r ./logs ./logs_backup_$timestamp
        log "Logs backed up to logs_backup_$timestamp"
    fi
}

pull_latest_image() {
    log "Pulling latest Docker image..."
    docker-compose pull
    log "Image pulled successfully"
}

stop_services() {
    log "Stopping existing services..."
    docker-compose down || true
    
    # Forcefully remove container if it's still running
    if docker ps -q --filter "name=$CONTAINER_NAME" | grep -q .; then
        warn "Force stopping container $CONTAINER_NAME"
        docker stop $CONTAINER_NAME || true
        docker rm $CONTAINER_NAME || true
    fi
    
    log "Services stopped"
}

start_services() {
    log "Starting services..."
    docker-compose up -d
    log "Services started"
}

wait_for_health() {
    log "Waiting for application to become healthy..."
    
    for i in $(seq 1 $MAX_HEALTH_CHECKS); do
        if curl -f $HEALTH_URL > /dev/null 2>&1; then
            log "Application is healthy! ✅"
            return 0
        fi
        
        echo -n "."
        sleep 10
    done
    
    error "Application health check failed after $MAX_HEALTH_CHECKS attempts"
    return 1
}

cleanup_old_images() {
    log "Cleaning up old Docker images..."
    docker image prune -f
    log "Cleanup completed"
}

rollback() {
    error "Deployment failed! Attempting rollback..."
    
    # Try to start the previous version
    docker-compose down || true
    
    # Check if there's a backup image
    if docker images | grep -q "$CONTAINER_NAME.*backup"; then
        warn "Attempting to restore from backup image..."
        # This would need to be implemented based on your backup strategy
    fi
    
    error "Rollback completed. Please check logs and fix the issue."
    exit 1
}

main() {
    log "Starting deployment process..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml not found. Are you in the correct directory?"
        exit 1
    fi
    
    # Pre-deployment checks
    check_dependencies
    backup_logs
    
    # Deployment process
    pull_latest_image
    stop_services
    start_services
    
    # Post-deployment verification
    if wait_for_health; then
        cleanup_old_images
        log "🚀 Deployment completed successfully!"
        log "🔗 Health check: $HEALTH_URL"
        log "📊 Container status:"
        docker-compose ps
    else
        rollback
    fi
}

# Handle script interruption
trap 'error "Deployment interrupted!"; rollback' INT TERM

# Run main function
main "$@"