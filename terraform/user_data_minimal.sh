#!/bin/bash
# Minimal user data script to avoid boot issues
set -e

# Update package list only (no upgrades)
apt-get update

# Install Docker (essential only)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install minimal tools
apt-get install -y curl

# Create app directory
mkdir -p /opt/expense-tracker
chown ubuntu:ubuntu /opt/expense-tracker

echo "Minimal bootstrap completed" > /var/log/bootstrap.log
