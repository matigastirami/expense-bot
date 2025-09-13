terraform {
  required_version = ">= 1.0"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "digitalocean" {
  token = var.do_token
}

# SSH Key (commented out for import - you can add later)
# resource "digitalocean_ssh_key" "main" {
#   name       = "${var.project_name}-key"
#   public_key = var.ssh_public_key
# }

# Droplet (this will represent your existing droplet)
resource "digitalocean_droplet" "main" {
  image      = "ubuntu-24-04-x64"
  name       = "expensegram-bot"
  region     = "nyc3"
  size       = "s-1vcpu-1gb"
  monitoring = true

  # ssh_keys = [digitalocean_ssh_key.main.fingerprint]  # Commented out for import

  # user_data = file("${path.module}/user_data.sh")  # Commented out for import

  tags = ["${var.project_name}", var.environment]
}

# Firewall
resource "digitalocean_firewall" "main" {
  name = "${var.project_name}-firewall"

  droplet_ids = [digitalocean_droplet.main.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "8000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
