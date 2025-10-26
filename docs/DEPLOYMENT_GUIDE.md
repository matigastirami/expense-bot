# Production Deployment Guide - Hetzner Server

This guide will walk you through deploying the Expense Tracker application to your Hetzner server with your GoDaddy domain.

## Prerequisites

- Hetzner server running Ubuntu 20.04+ or Debian 11+
- Domain purchased from GoDaddy (e.g., `yourdomain.com`)
- Supabase account with PostgreSQL database
- Telegram Bot Token from @BotFather
- OpenAI API Key

## Table of Contents

1. [Server Initial Setup](#1-server-initial-setup)
2. [Domain Configuration (GoDaddy)](#2-domain-configuration-godaddy)
3. [Install Dependencies](#3-install-dependencies)
4. [Configure Application](#4-configure-application)
5. [Setup SSL with Let's Encrypt](#5-setup-ssl-with-lets-encrypt)
6. [Deploy Application](#6-deploy-application)
7. [Monitoring & Maintenance](#7-monitoring--maintenance)

---

## 1. Server Initial Setup

### Connect to Your Hetzner Server

```bash
ssh root@your-server-ip
```

### Create a Non-Root User (Recommended)

```bash
# Create user
adduser expense

# Add to sudo group
usermod -aG sudo expense

# Add to docker group (we'll install Docker later)
usermod -aG docker expense

# Switch to new user
su - expense
```

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Configure Firewall

```bash
# Install ufw if not already installed
sudo apt install ufw

# Allow SSH
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 2. Domain Configuration (GoDaddy)

### Configure DNS Records

1. Log in to your GoDaddy account
2. Go to "My Products" → "Domains" → Select your domain → "DNS"
3. Add/Edit the following records:

| Type  | Name | Value             | TTL  |
|-------|------|-------------------|------|
| A     | @    | your-server-ip    | 600  |
| A     | www  | your-server-ip    | 600  |
| A     | api  | your-server-ip    | 600  |
| CNAME | www  | yourdomain.com    | 3600 |

**Note:** DNS propagation can take up to 48 hours, but usually completes within 1-2 hours.

### Verify DNS Propagation

```bash
# Check if domain resolves to your server
dig yourdomain.com +short
dig www.yourdomain.com +short
dig api.yourdomain.com +short

# Or use nslookup
nslookup yourdomain.com
```

---

## 3. Install Dependencies

### Install Docker

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Install Docker Compose (Standalone)

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Install Certbot (for SSL)

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Install Git

```bash
sudo apt install -y git
git --version
```

---

## 4. Configure Application

### Clone Repository

```bash
# Create directory for the app
mkdir -p ~/apps
cd ~/apps

# Clone your repository
git clone https://github.com/yourusername/expense-tracker-claude.git
cd expense-tracker-claude
```

### Create Production Environment File

```bash
# Copy the production template
cp .env.production .env

# Edit with your actual values
nano .env
```

**Fill in these critical values:**

```bash
# Supabase Database (from Supabase Dashboard > Project Settings > Database)
POSTGRES_HOST=db.xxxxxxxxxxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-actual-supabase-password

# API Configuration
API_BASE_URL=https://api.yourdomain.com

# Generate a secure JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Telegram Bot (from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_NAME=your_bot_username

# OpenAI
OPENAI_API_KEY=sk-your-actual-key
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

### Generate JWT Secret

```bash
# Generate a secure random string
openssl rand -hex 32

# Copy the output and paste it as JWT_SECRET in your .env file
```

---

## 5. Setup SSL with Let's Encrypt

### Configure Nginx

```bash
# Copy the nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/expense-tracker

# Replace 'yourdomain.com' with your actual domain
sudo sed -i 's/yourdomain.com/expensgram.xyz/g' /etc/nginx/sites-available/expense-tracker

# Or manually edit the file
sudo nano /etc/nginx/sites-available/expense-tracker
```

### Enable the Site (Without SSL first)

```bash
# Create temporary HTTP-only config for Certbot
sudo tee /etc/nginx/sites-available/expense-tracker-temp > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com api.yourdomain.com;

    location / {
        return 200 "Server is ready for SSL setup";
        add_header Content-Type text/plain;
    }
}
EOF

# Replace with your domain
sudo sed -i 's/yourdomain.com/expensgram.xyz/g' /etc/nginx/sites-available/expense-tracker-temp

# Enable temporary config
sudo ln -sf /etc/nginx/sites-available/expense-tracker-temp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Obtain SSL Certificate

```bash
# Request certificate for all domains
sudo certbot certonly --nginx \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Replace with your actual domain and email
```

### Enable Full Nginx Configuration with SSL

```bash
# Remove temporary config
sudo rm /etc/nginx/sites-enabled/expense-tracker-temp

# Enable the full configuration with SSL
sudo ln -s /etc/nginx/sites-available/expense-tracker /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Auto-Renewal Setup

```bash
# Certbot auto-renewal is already configured
# Test renewal process
sudo certbot renew --dry-run

# Check auto-renewal timer
sudo systemctl status certbot.timer
```

---

## 6. Deploy Application

### Run Deployment Script

```bash
cd ~/apps/expense-tracker-claude

# Make deploy script executable (if not already)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
1. Pull latest code from git
2. Stop existing containers
3. Build Docker images
4. Run database migrations on Supabase
5. Start all services (API, Web, Telegram Bot)
6. Verify health

### Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test API health
curl https://api.yourdomain.com/health

# Test web
curl https://yourdomain.com
```

### Test Telegram Bot

1. Open Telegram
2. Search for your bot: `@your_bot_username`
3. Send `/start`
4. You should receive a welcome message

---

## 7. Monitoring & Maintenance

### Useful Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f bot
docker-compose -f docker-compose.prod.yml logs -f web

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check resource usage
docker stats
```

### Update Application

```bash
cd ~/apps/expense-tracker-claude

# Pull latest changes
git pull origin main

# Redeploy
./deploy.sh
```

### Database Backups

Since you're using Supabase, backups are handled automatically. However, you can create manual backups:

```bash
# Export database schema and data
pg_dump -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -F c \
  -f backup_$(date +%Y%m%d_%H%M%S).dump

# Or use Supabase Dashboard: Settings > Database > Backups
```

### Monitor Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Clean up old logs
sudo journalctl --vacuum-time=7d
```

### Setup Automatic Updates (Optional)

```bash
# Create update script
cat > ~/apps/expense-tracker-claude/auto-update.sh <<'EOF'
#!/bin/bash
cd ~/apps/expense-tracker-claude
git pull origin main
./deploy.sh >> ~/logs/deploy.log 2>&1
EOF

chmod +x ~/apps/expense-tracker-claude/auto-update.sh

# Add to crontab (runs daily at 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * * ~/apps/expense-tracker-claude/auto-update.sh") | crontab -
```

### Monitor Application Health

```bash
# Create monitoring script
cat > ~/monitor.sh <<'EOF'
#!/bin/bash

# Check API
if curl -f https://api.yourdomain.com/health > /dev/null 2>&1; then
    echo "✓ API is healthy"
else
    echo "✗ API is down!"
    # Add notification (email, Telegram, etc.)
fi

# Check Web
if curl -f https://yourdomain.com > /dev/null 2>&1; then
    echo "✓ Web is healthy"
else
    echo "✗ Web is down!"
fi

# Check containers
docker-compose -f ~/apps/expense-tracker-claude/docker-compose.prod.yml ps
EOF

chmod +x ~/monitor.sh

# Run monitoring every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/monitor.sh >> ~/logs/monitor.log 2>&1") | crontab -
```

---

## Troubleshooting

### API Not Responding

```bash
# Check API logs
docker-compose -f docker-compose.prod.yml logs api

# Restart API
docker-compose -f docker-compose.prod.yml restart api
```

### Telegram Bot Not Responding

```bash
# Check bot logs
docker-compose -f docker-compose.prod.yml logs bot

# Verify token in .env
cat .env | grep TELEGRAM_BOT_TOKEN

# Restart bot
docker-compose -f docker-compose.prod.yml restart bot
```

### Database Connection Issues

```bash
# Test database connection
docker run --rm \
  -e POSTGRES_HOST="your-host" \
  -e POSTGRES_USER="postgres" \
  -e POSTGRES_PASSWORD="your-password" \
  postgres:15-alpine \
  psql -h your-host -U postgres -c "SELECT version();"

# Check if Supabase IP is whitelisted (if using IP restrictions)
```

### SSL Certificate Issues

```bash
# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a --volumes -f

# Clean old logs
sudo journalctl --vacuum-size=100M

# Check large files
sudo du -h --max-depth=1 / | sort -hr | head -20
```

---

## Security Best Practices

### 1. Keep System Updated

```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y
```

### 2. Configure Fail2Ban (Optional)

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Secure SSH

Edit `/etc/ssh/sshd_config`:

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:
```bash
sudo systemctl restart ssh
```

### 4. Regular Backups

- Supabase handles database backups automatically
- Backup your `.env` file securely
- Consider backing up Docker volumes periodically

---

## Next Steps

1. **Monitor your application** - Check logs regularly
2. **Set up monitoring** - Consider using services like UptimeRobot
3. **Configure analytics** - Add Google Analytics or similar
4. **Setup alerts** - Configure notifications for downtime
5. **Performance tuning** - Optimize based on usage patterns

---

## Support & Resources

- **Logs location:**
  - Nginx: `/var/log/nginx/`
  - Application: `docker-compose logs`

- **Configuration files:**
  - Nginx: `/etc/nginx/sites-available/expense-tracker`
  - Environment: `~/apps/expense-tracker-claude/.env`

- **Useful links:**
  - Hetzner Docs: https://docs.hetzner.com/
  - Let's Encrypt: https://letsencrypt.org/
  - Docker Compose: https://docs.docker.com/compose/
  - Supabase: https://supabase.com/docs

---

**Congratulations!** Your Expense Tracker is now deployed to production! 🎉
