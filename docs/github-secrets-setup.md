# GitHub Secrets Configuration Guide

This document provides detailed instructions for setting up GitHub Secrets for the AWS Lightsail deployment.

## 🔑 Required Secrets

### Infrastructure Secrets (Terraform)

| Secret Name | Description | Example Value | Required |
|-------------|-------------|---------------|----------|
| `AWS_ACCESS_KEY_ID` | AWS IAM Access Key | `AKIAIOSFODNN7EXAMPLE` | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM Secret Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | ✅ |

### Deployment Secrets

| Secret Name | Description | Example Value | Required |
|-------------|-------------|---------------|----------|
| `LIGHTSAIL_HOST` | Static IP from Terraform | `203.0.113.1` | ✅ |
| `LIGHTSAIL_SSH_KEY` | Private SSH key from Terraform | `-----BEGIN RSA PRIVATE KEY-----\n...` | ✅ |

### Application Secrets

| Secret Name | Description | Example Value | Required |
|-------------|-------------|---------------|----------|
| `POSTGRES_HOST` | Supabase database host | `db.abcdefghijklmnop.supabase.co` | ✅ |
| `POSTGRES_PORT` | Database port | `5432` | ✅ |
| `POSTGRES_DB` | Database name | `postgres` | ✅ |
| `POSTGRES_USER` | Database username | `postgres` | ✅ |
| `POSTGRES_PASSWORD` | Database password | `your-secure-password` | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` | ✅ |

## 📝 Step-by-Step Setup

### 1. Navigate to GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** tab
3. In the left sidebar, click **Secrets and variables**
4. Click **Actions**

### 2. Add Infrastructure Secrets First

#### AWS_ACCESS_KEY_ID
```
Name: AWS_ACCESS_KEY_ID
Value: AKIAIOSFODNN7EXAMPLE
```

#### AWS_SECRET_ACCESS_KEY
```
Name: AWS_SECRET_ACCESS_KEY
Value: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 3. Run Terraform to Create Infrastructure

After adding AWS credentials, push a change to the `terraform/` directory or manually trigger the Terraform workflow. This will create your Lightsail instance and generate the required SSH keys.

### 4. Extract Terraform Outputs

From the Terraform workflow logs, or by running locally:

```bash
# Get static IP
terraform output static_ip

# Get private key (sensitive)
terraform output -raw private_key
```

### 5. Add Deployment Secrets

#### LIGHTSAIL_HOST
```
Name: LIGHTSAIL_HOST
Value: 203.0.113.1
```

#### LIGHTSAIL_SSH_KEY
```
Name: LIGHTSAIL_SSH_KEY
Value: -----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(complete private key content)
...
-----END RSA PRIVATE KEY-----
```

⚠️ **Important**: Include the entire private key including the `-----BEGIN` and `-----END` lines.

### 6. Add Application Secrets

#### Database Configuration (Supabase)

Get these from your Supabase dashboard under **Settings → Database**:

```
Name: POSTGRES_HOST
Value: db.abcdefghijklmnop.supabase.co
```

```
Name: POSTGRES_PORT
Value: 5432
```

```
Name: POSTGRES_DB
Value: postgres
```

```
Name: POSTGRES_USER
Value: postgres
```

```
Name: POSTGRES_PASSWORD
Value: your-supabase-database-password
```

#### API Keys

```
Name: TELEGRAM_BOT_TOKEN
Value: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

```
Name: OPENAI_API_KEY
Value: sk-proj-abcdefghijklmnopqrstuvwxyz
```

## 🔍 Verification

### Check All Secrets Are Added

Your secrets list should include all of these:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY
- ✅ LIGHTSAIL_HOST
- ✅ LIGHTSAIL_SSH_KEY
- ✅ POSTGRES_HOST
- ✅ POSTGRES_PORT
- ✅ POSTGRES_DB
- ✅ POSTGRES_USER
- ✅ POSTGRES_PASSWORD
- ✅ TELEGRAM_BOT_TOKEN
- ✅ OPENAI_API_KEY

### Test Deployment

Once all secrets are configured, trigger a deployment by pushing any code change:

```bash
git add .
git commit -m "test: trigger deployment"
git push origin main
```

Monitor the GitHub Actions workflow to ensure it completes successfully.

## 🐛 Troubleshooting Secrets

### Common Issues

#### 1. SSH Key Format Issues
**Problem**: SSH connection fails with key format errors
**Solution**: Ensure the private key includes the complete header and footer:
```
-----BEGIN RSA PRIVATE KEY-----
[key content]
-----END RSA PRIVATE KEY-----
```

#### 2. Multi-line Secrets
**Problem**: Private key or other multi-line secrets not working
**Solution**: When copying the private key, ensure all line breaks are preserved. GitHub Secrets handles multi-line values correctly when pasted as-is.

#### 3. Special Characters in Secrets
**Problem**: Passwords with special characters causing issues
**Solution**: GitHub Secrets handle special characters automatically. If issues persist, try URL-encoding the password.

#### 4. Missing Secrets
**Problem**: Workflow fails with "secret not found"
**Solution**: Double-check spelling and ensure all required secrets are added.

### Testing Individual Secrets

You can test secrets by temporarily adding debug steps to your workflow:

```yaml
- name: Debug Secrets (REMOVE IN PRODUCTION)
  run: |
    echo "Host: ${{ secrets.LIGHTSAIL_HOST }}"
    echo "DB Host: ${{ secrets.POSTGRES_HOST }}"
    echo "SSH key length: ${#LIGHTSAIL_SSH_KEY}"
  env:
    LIGHTSAIL_SSH_KEY: ${{ secrets.LIGHTSAIL_SSH_KEY }}
```

⚠️ **Security Warning**: Never echo sensitive secrets in production workflows!

## 🔄 Updating Secrets

To update a secret:
1. Go to **Settings → Secrets and variables → Actions**
2. Click the **Update** button next to the secret name
3. Enter the new value
4. Click **Update secret**

Changes take effect immediately for new workflow runs.

## 🔒 Security Best Practices

1. **Principle of Least Privilege**: Only grant the minimum AWS permissions needed
2. **Regular Rotation**: Rotate API keys and passwords regularly
3. **Monitor Usage**: Review GitHub Actions logs for unusual activity
4. **Environment Isolation**: Use different secrets for dev/staging/prod environments
5. **Access Control**: Limit who can modify repository secrets

## 📋 Secrets Checklist

Before running deployment, verify:

- [ ] All 11 required secrets are added
- [ ] AWS credentials have correct permissions
- [ ] Terraform has been run and outputs obtained
- [ ] SSH key is complete with headers/footers
- [ ] Supabase connection details are correct
- [ ] API keys are valid and active
- [ ] No typos in secret names
- [ ] Multi-line secrets are formatted correctly

## 🆘 Getting Help

If you're having trouble with secrets configuration:

1. **Check the deployment logs** in GitHub Actions for specific error messages
2. **Verify each secret individually** by temporarily debugging (safely)
3. **Test Supabase connection** locally first
4. **Regenerate keys** if you suspect they're compromised
5. **Review AWS IAM permissions** if Terraform fails

Remember: Secret values are never displayed in GitHub UI for security reasons, so double-check your sources when copying values.