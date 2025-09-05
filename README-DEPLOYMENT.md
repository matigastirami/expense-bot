# 🚀 AWS Lightsail Deployment

This project includes a complete production deployment setup using **Terraform** for infrastructure and **GitHub Actions** for automated deployments to **AWS Lightsail**.

## ⚡ Quick Start

1. **Set up AWS credentials** in GitHub Secrets
2. **Push to main branch** to trigger infrastructure creation
3. **Configure remaining secrets** from Terraform outputs  
4. **Deploy automatically** on every code push

**Total monthly cost: $3.50** (Lightsail nano instance)

## 📁 Deployment Files

```
├── terraform/                 # Infrastructure as Code
│   ├── main.tf                # Lightsail instance, networking
│   ├── variables.tf           # Configuration variables  
│   ├── outputs.tf             # SSH keys, IP addresses
│   └── user_data.sh           # Server bootstrap script
├── .github/workflows/         # CI/CD Automation
│   ├── deploy.yml             # Application deployment
│   └── terraform.yml          # Infrastructure deployment
├── scripts/                   # Deployment utilities
│   ├── deploy.sh              # Production deployment
│   ├── setup-server.sh        # Server configuration
│   └── health-check.sh        # Monitoring & health checks
├── Dockerfile.prod            # Production container
└── docker-compose.prod.yml    # Production orchestration
```

## 🏗️ Architecture

```
GitHub → Actions → Docker Registry → Lightsail → Supabase
   ↓        ↓           ↓             ↓          ↓
  Code   Build/Test   Store Image   Run Bot   Database
```

**Components:**
- **Infrastructure**: AWS Lightsail nano ($3.50/month)
- **Database**: Supabase (your existing instance) 
- **CI/CD**: GitHub Actions (2000 min/month free)
- **Container Registry**: GitHub Container Registry (free)
- **Monitoring**: Built-in health checks + auto-restart

## 🎯 Features

- ✅ **Infrastructure as Code** with Terraform
- ✅ **Zero-downtime deployments** with health checks
- ✅ **Automatic SSL certificates** (Let's Encrypt ready)
- ✅ **Security hardening** (firewall, fail2ban, non-root containers)
- ✅ **Monitoring & alerting** with health check scripts
- ✅ **Log management** with rotation and cleanup
- ✅ **Cost optimization** ($3.50/month total)
- ✅ **Production ready** with proper error handling

## 🚀 Getting Started

### 1. Prerequisites

- AWS Account with programmatic access
- GitHub repository 
- Supabase database (your existing one)
- Telegram Bot Token
- OpenAI API Key

### 2. Quick Setup

```bash
# 1. Add AWS credentials to GitHub Secrets
#    AWS_ACCESS_KEY_ID
#    AWS_SECRET_ACCESS_KEY

# 2. Push to main branch (triggers infrastructure creation)
git add terraform/
git commit -m "feat: add infrastructure"
git push origin main

# 3. Get outputs from Terraform workflow and add to GitHub Secrets:
#    LIGHTSAIL_HOST (static IP)
#    LIGHTSAIL_SSH_KEY (private key)

# 4. Add your application secrets:
#    POSTGRES_HOST, POSTGRES_PASSWORD, etc.
#    TELEGRAM_BOT_TOKEN
#    OPENAI_API_KEY

# 5. Deploy application (automatically on any code push)
git add .
git commit -m "feat: deploy application"
git push origin main
```

### 3. Access Your Bot

After deployment:
- **Health Check**: `http://YOUR_IP:8000/health`
- **SSH Access**: `ssh ubuntu@YOUR_IP`
- **Logs**: `docker-compose logs -f`

## 📚 Documentation

- **[Complete Deployment Guide](docs/deployment.md)** - Step-by-step instructions
- **[GitHub Secrets Setup](docs/github-secrets-setup.md)** - Security configuration
- **[Server Management](docs/deployment.md#server-management)** - Operations guide

## 🛠️ Manual Operations

```bash
# SSH to server
ssh ubuntu@YOUR_SERVER_IP

# Deploy manually
cd /opt/expense-tracker
./scripts/deploy.sh

# Health check  
./scripts/health-check.sh --auto-restart

# View logs
docker-compose logs -f
tail -f logs/health-check.log

# Restart service
docker-compose restart
```

## 🔍 Monitoring

The deployment includes comprehensive monitoring:

- **Health Endpoint**: HTTP health check on port 8000
- **Container Health**: Docker healthcheck with auto-restart
- **System Monitoring**: CPU, memory, disk space alerts
- **Log Aggregation**: Centralized logging with rotation
- **Auto-Recovery**: Automatic service restart on failure

## 💰 Cost Breakdown

| Component | Monthly Cost |
|-----------|-------------|
| AWS Lightsail nano | $3.50 |
| Supabase | $0 (existing) |
| GitHub Actions | $0 (free tier) |
| **Total** | **$3.50** |

## 🔒 Security Features

- **Firewall**: UFW with minimal open ports (22, 80, 443, 8000)
- **SSH Protection**: fail2ban prevents brute force attacks  
- **Container Security**: Non-root user, minimal base image
- **Network Security**: Private container networking
- **Secrets Management**: Environment variables, no hardcoded secrets
- **Auto Updates**: System packages kept current

## 📈 Scaling Options

**Current Setup (nano)**: Perfect for personal use
- 1 vCPU, 512MB RAM, 20GB SSD
- Handles ~100-1000 messages/day easily

**Scale Up Options**:
- **micro_2_0**: $5/month (1 vCPU, 1GB RAM) - 2x capacity
- **small_2_0**: $10/month (1 vCPU, 2GB RAM) - 4x capacity

**Scale Out**: Add load balancer + multiple instances for high availability

## 🐛 Troubleshooting

**Common Issues:**

1. **Health check fails**: `curl http://localhost:8000/health`
2. **SSH issues**: Verify key format and security groups
3. **Database connection**: Test Supabase connectivity
4. **Deployment fails**: Check GitHub Actions logs

**Quick Fixes:**
```bash
# Restart everything
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs app | tail -50

# System resources  
htop && df -h && free -m
```

## 🔄 CI/CD Pipeline

**On every push to main:**

1. **Build Stage**:
   - Build production Docker image
   - Run security scans
   - Push to GitHub Container Registry

2. **Deploy Stage**:
   - SSH to Lightsail instance
   - Pull latest image
   - Zero-downtime container swap
   - Health check verification
   - Cleanup old images

3. **Verify Stage**:
   - External health check
   - Smoke tests
   - Notification (success/failure)

## ✨ What's Included

This deployment setup provides everything you need for a production Telegram bot:

- 🏗️ **Infrastructure**: Terraform-managed AWS resources
- 🚀 **Deployment**: Automated GitHub Actions pipeline  
- 📦 **Containerization**: Production-ready Docker setup
- 🔍 **Monitoring**: Health checks and automated recovery
- 🔒 **Security**: Hardened server with best practices
- 📊 **Logging**: Structured logs with rotation
- 💰 **Cost-Effective**: Only $3.50/month operating cost
- 📚 **Documentation**: Complete setup and operations guide

---

**Ready to deploy?** Start with the [Complete Deployment Guide](docs/deployment.md)!