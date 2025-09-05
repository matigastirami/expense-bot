#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    error "Please run this script as a regular user, not as root"
    exit 1
fi

install_docker() {
    log "Installing Docker..."
    
    # Remove old versions
    sudo apt-get remove docker docker-engine docker.io containerd runc || true
    
    # Update apt package index
    sudo apt-get update
    
    # Install packages to allow apt to use a repository over HTTPS
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    log "Docker installed successfully"
}

install_docker_compose() {
    log "Installing Docker Compose..."
    
    # Get latest version
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    
    # Download and install
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    log "Docker Compose installed successfully"
}

setup_firewall() {
    log "Configuring UFW firewall..."
    
    # Install UFW if not already installed
    sudo apt-get install -y ufw
    
    # Reset to defaults
    sudo ufw --force reset
    
    # Set defaults
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow health check port
    sudo ufw allow 8000/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    log "Firewall configured successfully"
}

setup_fail2ban() {
    log "Setting up fail2ban for SSH protection..."
    
    sudo apt-get install -y fail2ban
    
    # Create jail.local configuration
    sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF
    
    # Restart and enable fail2ban
    sudo systemctl restart fail2ban
    sudo systemctl enable fail2ban
    
    log "fail2ban configured successfully"
}

create_app_directory() {
    log "Creating application directory..."
    
    APP_DIR="/opt/expense-tracker"
    
    # Create directory with proper permissions
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    
    # Create subdirectories
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/backups
    
    log "Application directory created at $APP_DIR"
}

setup_logrotate() {
    log "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/expense-tracker > /dev/null << 'EOF'
/opt/expense-tracker/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        /usr/bin/docker kill --signal=HUP expense-tracker-bot 2>/dev/null || true
    endscript
}
EOF
    
    log "Log rotation configured"
}

setup_systemd_service() {
    log "Setting up systemd service..."
    
    sudo tee /etc/systemd/system/expense-tracker.service > /dev/null << EOF
[Unit]
Description=Expense Tracker Telegram Bot
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/expense-tracker
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable expense-tracker
    
    log "Systemd service configured"
}

install_monitoring_tools() {
    log "Installing monitoring tools..."
    
    sudo apt-get install -y htop iotop nethogs ncdu
    
    log "Monitoring tools installed"
}

setup_swap() {
    log "Setting up swap file..."
    
    # Check if swap already exists
    if swapon --show | grep -q /swapfile; then
        warn "Swap file already exists, skipping..."
        return
    fi
    
    # Create 1GB swap file
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    
    # Make swap permanent
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    
    # Configure swappiness
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    
    log "Swap file created and configured"
}

optimize_system() {
    log "Optimizing system settings..."
    
    # Update system
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Install essential packages
    sudo apt-get install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    # Set timezone to UTC
    sudo timedatectl set-timezone UTC
    
    log "System optimization completed"
}

display_summary() {
    info "🎉 Server setup completed successfully!"
    echo ""
    info "📋 Summary of installed components:"
    info "  ✅ Docker and Docker Compose"
    info "  ✅ UFW Firewall (SSH, HTTP, HTTPS, port 8000 allowed)"
    info "  ✅ fail2ban (SSH protection)"
    info "  ✅ Application directory: /opt/expense-tracker"
    info "  ✅ Log rotation configured"
    info "  ✅ Systemd service configured"
    info "  ✅ 1GB swap file"
    info "  ✅ Monitoring tools"
    echo ""
    warn "⚠️  IMPORTANT: You need to log out and log back in for Docker group changes to take effect"
    echo ""
    info "🚀 Next steps:"
    info "  1. Log out and log back in (or run: newgrp docker)"
    info "  2. Navigate to /opt/expense-tracker"
    info "  3. Create your docker-compose.yml file"
    info "  4. Set up your environment variables"
    info "  5. Run: docker-compose up -d"
    echo ""
    info "🔗 Useful commands:"
    info "  - Check service status: sudo systemctl status expense-tracker"
    info "  - View logs: docker-compose logs -f"
    info "  - Check firewall status: sudo ufw status"
    info "  - Check fail2ban status: sudo fail2ban-client status"
}

main() {
    log "🚀 Starting Expense Tracker server setup..."
    echo ""
    
    optimize_system
    install_docker
    install_docker_compose
    setup_firewall
    setup_fail2ban
    create_app_directory
    setup_logrotate
    setup_systemd_service
    install_monitoring_tools
    setup_swap
    
    display_summary
}

# Handle script interruption
trap 'error "Setup interrupted!"' INT TERM

# Run main function
main "$@"