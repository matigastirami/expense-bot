output "droplet_name" {
  description = "Name of the DigitalOcean droplet"
  value       = digitalocean_droplet.main.name
}

output "droplet_ip" {
  description = "Public IP address of the droplet"
  value       = digitalocean_droplet.main.ipv4_address
}

output "droplet_id" {
  description = "ID of the DigitalOcean droplet"
  value       = digitalocean_droplet.main.id
}

# output "ssh_key_name" {
#   description = "Name of the SSH key"
#   value       = digitalocean_ssh_key.main.name
# }

# output "ssh_key_fingerprint" {
#   description = "Fingerprint of the SSH key"
#   value       = digitalocean_ssh_key.main.fingerprint
# }

output "instance_username" {
  description = "Username for SSH access"
  value       = "root"
}

output "health_check_url" {
  description = "Health check URL for the bot"
  value       = "http://${digitalocean_droplet.main.ipv4_address}:8000/health"
}

output "firewall_id" {
  description = "ID of the firewall"
  value       = digitalocean_firewall.main.id
}
