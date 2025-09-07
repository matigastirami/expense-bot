variable "aws_region" {
  description = "AWS region for Lightsail resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "expense-tracker"
}

variable "instance_name" {
  description = "Name of the Lightsail instance"
  type        = string
  default     = "expense-tracker-bot"
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

# GitHub configuration for auto-updating secrets (commented out for now)
# variable "github_token" {
#   description = "GitHub personal access token"
#   type        = string
#   sensitive   = true
# }

# variable "github_owner" {
#   description = "GitHub repository owner/organization"
#   type        = string
#   default     = "matigastirami"
# }

# variable "github_repo" {
#   description = "GitHub repository name"
#   type        = string
#   default     = "expense-bot"
# }
