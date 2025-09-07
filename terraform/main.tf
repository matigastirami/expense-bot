terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket = "expense-bot-tf-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# SSH Key Pair for instance access
resource "aws_lightsail_key_pair" "main" {
  name = "${var.project_name}-key"
}

# Lightsail instance
resource "aws_lightsail_instance" "main" {
  name              = var.instance_name
  availability_zone = "${var.aws_region}a"
  blueprint_id      = "ubuntu_22_04"
  bundle_id         = "nano_2_0" # $3.50/month - 1 vCPU, 512 MB RAM, 20 GB SSD
  key_pair_name     = aws_lightsail_key_pair.main.name

  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name        = var.instance_name
    Environment = var.environment
    Project     = var.project_name
  }
}

# Static IP
resource "aws_lightsail_static_ip" "main" {
  name = "${var.project_name}-static-ip"
}

# Attach static IP to instance
resource "aws_lightsail_static_ip_attachment" "main" {
  static_ip_name = aws_lightsail_static_ip.main.name
  instance_name  = aws_lightsail_instance.main.name
}

# Open firewall ports
resource "aws_lightsail_instance_public_ports" "main" {
  instance_name = aws_lightsail_instance.main.name

  port_info {
    protocol  = "tcp"
    from_port = 22
    to_port   = 22
    cidrs     = ["0.0.0.0/0"] # SSH access
  }

  port_info {
    protocol  = "tcp"
    from_port = 80
    to_port   = 80
    cidrs     = ["0.0.0.0/0"] # HTTP
  }

  port_info {
    protocol  = "tcp"
    from_port = 443
    to_port   = 443
    cidrs     = ["0.0.0.0/0"] # HTTPS
  }

  port_info {
    protocol  = "tcp"
    from_port = 8000
    to_port   = 8000
    cidrs     = ["0.0.0.0/0"] # Bot health check port
  }
}
