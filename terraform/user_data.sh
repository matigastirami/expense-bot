#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install useful tools
apt-get install -y git curl wget htop unzip fail2ban ufw

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 8000
ufw --force enable

# Configure fail2ban for SSH protection
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

echo "Server bootstrap completed successfully" > /var/log/bootstrap.log