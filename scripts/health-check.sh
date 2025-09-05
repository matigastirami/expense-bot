#!/bin/bash

# Health check script for monitoring the expense tracker bot
# Can be used with cron jobs for automated monitoring

set -e

# Configuration
HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/opt/expense-tracker/logs/health-check.log"
MAX_RETRIES=3
RETRY_DELAY=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1" >> $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1" >> $LOG_FILE
}

check_health() {
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if curl -f -s --max-time 10 $HEALTH_URL > /dev/null 2>&1; then
            log "Health check passed ✅"
            return 0
        else
            retry_count=$((retry_count + 1))
            warn "Health check failed (attempt $retry_count/$MAX_RETRIES)"
            
            if [ $retry_count -lt $MAX_RETRIES ]; then
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    error "Health check failed after $MAX_RETRIES attempts ❌"
    return 1
}

check_container_status() {
    local container_name="expense-tracker-bot"
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        log "Container $container_name is running ✅"
        return 0
    else
        error "Container $container_name is not running ❌"
        
        # Try to get container status
        if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name"; then
            local status=$(docker ps -a --format "{{.Status}}" --filter "name=$container_name")
            error "Container status: $status"
        else
            error "Container $container_name not found"
        fi
        
        return 1
    fi
}

check_disk_space() {
    local threshold=90
    local usage=$(df /opt/expense-tracker | awk 'NR==2 {print int($5)}')
    
    if [ $usage -gt $threshold ]; then
        error "Disk usage is $usage% (threshold: $threshold%) ❌"
        return 1
    else
        log "Disk usage is $usage% ✅"
        return 0
    fi
}

check_memory_usage() {
    local threshold=90
    local usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100.0}')
    
    if [ $usage -gt $threshold ]; then
        warn "Memory usage is $usage% (threshold: $threshold%) ⚠️"
        return 1
    else
        log "Memory usage is $usage% ✅"
        return 0
    fi
}

restart_service() {
    log "Attempting to restart the service..."
    
    cd /opt/expense-tracker
    
    # Try graceful restart first
    if docker-compose restart; then
        log "Service restarted successfully"
        sleep 30  # Give it time to start up
        
        if check_health; then
            log "Service is healthy after restart ✅"
            return 0
        fi
    fi
    
    error "Failed to restart service or service is still unhealthy ❌"
    return 1
}

send_notification() {
    local message="$1"
    local severity="$2"
    
    # Log the notification
    if [ "$severity" = "error" ]; then
        error "ALERT: $message"
    elif [ "$severity" = "warning" ]; then
        warn "ALERT: $message"
    else
        log "ALERT: $message"
    fi
    
    # Here you could add integrations for:
    # - Slack webhooks
    # - Discord webhooks
    # - Email notifications
    # - SMS notifications
    # Example:
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"🤖 Expense Tracker Alert: $message\"}" \
    #   "$SLACK_WEBHOOK_URL"
}

main() {
    # Ensure log directory exists
    mkdir -p "$(dirname $LOG_FILE)"
    
    log "Starting health check..."
    
    local issues=0
    
    # Check container status
    if ! check_container_status; then
        issues=$((issues + 1))
        send_notification "Container is not running" "error"
    fi
    
    # Check health endpoint
    if ! check_health; then
        issues=$((issues + 1))
        send_notification "Health endpoint is not responding" "error"
    fi
    
    # Check system resources
    if ! check_disk_space; then
        issues=$((issues + 1))
        send_notification "Disk space is running low" "warning"
    fi
    
    if ! check_memory_usage; then
        issues=$((issues + 1))
        send_notification "Memory usage is high" "warning"
    fi
    
    # If there are critical issues, try to restart
    if [ $issues -gt 0 ]; then
        if [ "$1" = "--auto-restart" ]; then
            warn "Found $issues issues, attempting automatic restart..."
            if restart_service; then
                send_notification "Service automatically restarted and is now healthy" "info"
            else
                send_notification "Automatic restart failed, manual intervention required" "error"
                exit 1
            fi
        else
            error "Found $issues issues. Run with --auto-restart to attempt automatic recovery."
            exit 1
        fi
    else
        log "All health checks passed ✅"
    fi
    
    log "Health check completed"
}

# Handle script arguments
case "${1:-}" in
    --help)
        echo "Usage: $0 [--auto-restart] [--help]"
        echo ""
        echo "Options:"
        echo "  --auto-restart    Automatically restart the service if issues are detected"
        echo "  --help           Show this help message"
        echo ""
        echo "This script checks the health of the expense tracker bot and can optionally"
        echo "restart the service if problems are detected."
        echo ""
        echo "Add to crontab for automated monitoring:"
        echo "  */5 * * * * /opt/expense-tracker/scripts/health-check.sh --auto-restart"
        exit 0
        ;;
esac

# Run main function
main "$@"