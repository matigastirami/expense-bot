output "instance_name" {
  description = "Name of the Lightsail instance"
  value       = aws_lightsail_instance.main.name
}

output "static_ip" {
  description = "Static IP address of the instance"
  value       = aws_lightsail_static_ip.main.ip_address
}

output "ssh_key_name" {
  description = "Name of the SSH key pair"
  value       = aws_lightsail_key_pair.main.name
}

output "private_key" {
  description = "Private SSH key for instance access"
  value       = aws_lightsail_key_pair.main.private_key
  sensitive   = true
}

output "public_key" {
  description = "Public SSH key"
  value       = aws_lightsail_key_pair.main.public_key
}

output "instance_username" {
  description = "Username for SSH access"
  value       = "ubuntu"
}

output "health_check_url" {
  description = "Health check URL for the bot"
  value       = "http://${aws_lightsail_static_ip.main.ip_address}:8000/health"
}