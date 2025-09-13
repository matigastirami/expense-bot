variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

# variable "ssh_public_key" {
#   description = "SSH public key for droplet access"
#   type        = string
# }

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "expense-tracker"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Domain name for the bot (optional)"
  type        = string
  default     = ""
}
