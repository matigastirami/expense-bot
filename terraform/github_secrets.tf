# GitHub provider configuration
provider "github" {
  token = var.github_token
  owner = var.github_owner
}

# GitHub repository reference
data "github_repository" "repo" {
  name = var.github_repo
}

# Auto-update GitHub secrets with Lightsail info
resource "github_actions_secret" "lightsail_host" {
  repository      = data.github_repository.repo.name
  secret_name     = "LIGHTSAIL_HOST"
  plaintext_value = aws_lightsail_static_ip.main.ip_address
}

resource "github_actions_secret" "lightsail_ssh_key" {
  repository      = data.github_repository.repo.name
  secret_name     = "LIGHTSAIL_SSH_KEY"
  plaintext_value = aws_lightsail_key_pair.main.private_key
}
