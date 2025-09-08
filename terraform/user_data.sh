#!/bin/bash
set -e

# Log everything to a file for debugging
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting user data script at $(date)"

# Update system
echo "Updating system packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu
rm get-docker.sh

# Install Docker Compose
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify Docker installation
echo "Verifying Docker installation..."
systemctl enable docker
systemctl start docker
docker --version
docker-compose --version

# Install useful tools
echo "Installing additional tools..."
DEBIAN_FRONTEND=noninteractive apt-get install -y git curl wget htop unzip fail2ban ufw

# Ensure SSH service is running and enabled
echo "Ensuring SSH service is running..."
systemctl enable ssh
systemctl start ssh

# Verify SSH configuration
echo "Verifying SSH configuration..."
# Ensure SSH allows key authentication
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#AuthorizedKeysFile/AuthorizedKeysFile/' /etc/ssh/sshd_config
systemctl reload ssh
systemctl status ssh --no-pager

# Configure firewall (keeping it simple to avoid SSH lockout)
echo "Configuring basic firewall rules..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw --force enable

# Configure fail2ban for SSH protection
echo "Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Create app directory
mkdir -p /opt/expense-tracker
chown ubuntu:ubuntu /opt/expense-tracker

# Create systemd service for the bot
cat > /etc/systemd/system/expense-tracker.service << EOF
[Unit]
Description=Expense Tracker Telegram Bot
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/expense-tracker
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable but don't start the service yet (will be started by deployment)
systemctl enable expense-tracker

# Create log directory
mkdir -p /var/log/expense-tracker
chown ubuntu:ubuntu /var/log/expense-tracker

# Set up log rotation
cat > /etc/logrotate.d/expense-tracker << EOF
/var/log/expense-tracker/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
EOF

# Final verification
echo "Final system verification..."
systemctl status ssh --no-pager
systemctl status docker --no-pager
systemctl status fail2ban --no-pager

echo "Server bootstrap completed successfully at $(date)" | tee /var/log/bootstrap.log
echo "SSH should now be accessible"

# Test SSH access from localhost
echo "Testing local SSH access..."
ss -tlnp | grep :22 || echo "SSH port 22 not listening!"

echo "User data script completed successfully at $(date)"
