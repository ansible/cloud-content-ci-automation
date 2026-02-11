# GitHub-to-Jira Lambda Deployment

Simple Ansible playbook to deploy a Lambda function that syncs GitHub issues to Jira, with automatic daily scheduling.

## Files in This Directory

| File | Purpose |
|------|---------|
| **`deploy.yml`** | Main Ansible playbook - deploys Lambda + EventBridge schedule |
| **`requirements.yml`** | Ansible collections needed (amazon.aws, community.aws) |
| **`inventory.yml`** | Tells Ansible to run on localhost |
| **`ansible.cfg`** | Ansible configuration (output format, etc.) |
| **`vars.example.yml`** | Optional: Copy to `vars.yml` to customize settings |

## What It Does

When you run `deploy.yml`, it:

1. **Builds Lambda Package** - Runs `../lambda/build-lambda.sh` if deploy.zip doesn't exist
2. **Creates IAM Role** - With permissions to read Secrets Manager and write CloudWatch Logs
3. **Deploys Lambda Function** - Python 3.14 on ARM64 architecture
4. **Sets Up EventBridge Schedule** - Runs Lambda daily at 8 AM and 1 PM EST.
5. **Configures CloudWatch Logs** - 7-day retention for debugging

## Prerequisites

```bash
# 1. Install Ansible
pip install ansible

# 2. Install AWS collections
ansible-galaxy collection install -r requirements.yml

# 3. Configure AWS credentials
aws configure
# OR set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-2

# 4. Create Secrets Manager secret with Jira/GitHub credentials (if not present already)
aws secretsmanager create-secret \
  --name cloud_team_jira_login \
  --region us-east-2 \
  --secret-string '{
    "cloud_team_jira_bot_token": "your_jira_api_token",
    "cloud_team_jira_server": "https://issues.redhat.com",
    "cloud_team_gh_token": "ghp_your_github_token"
  }'
```

## How to Run

### Basic Deploy

```bash
ansible-playbook deploy.yml -e secret_name=cloud_team_jira_login
```

That's it! This deploys everything:
- Lambda function
- EventBridge schedule (runs daily at 10 AM UTC)
- IAM roles and policies
- CloudWatch Logs

### Customize Settings

```bash
ansible-playbook deploy.yml \
  -e secret_name=cloud_team_jira_login \
  -e aws_region=us-west-2 \
  -e lambda_timeout=600 \
  -e lambda_memory=512 \
  -e schedule_expression="cron(0 2 * * ? *)"
```

### Available Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `secret_name` | (required) | AWS Secrets Manager secret name |
| `aws_region` | `us-east-2` | AWS region to deploy to |
| `lambda_timeout` | `300` | Function timeout in seconds (max 900) |
| `lambda_memory` | `256` | Memory in MB (128-10240) |
| `schedule_expression` | `cron(0 10 * * ? *)` | When to run (daily at 10 AM UTC) |

### Schedule Expression Examples

```bash
# Daily at 2 AM UTC
-e schedule_expression="cron(0 2 * * ? *)"

# Every 6 hours
-e schedule_expression="cron(0 */6 * * ? *)"

# Monday-Friday at 9 AM UTC
-e schedule_expression="cron(0 9 ? * MON-FRI *)"
```

## After Deployment

### Test the Lambda

```bash
aws lambda invoke \
  --function-name github-to-jira-utility \
  --region us-east-2 \
  --payload '{}' \
  response.json

cat response.json
```

### View Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/github-to-jira-utility --region us-east-2 --follow

# View recent logs
aws logs tail /aws/lambda/github-to-jira-utility --region us-east-2 --since 1h
```

### Check EventBridge Schedule

```bash
aws events describe-rule --name github-jira-utility-daily-run --region us-east-2
```

## What Gets Created in AWS

- **Lambda Function**: `github-to-jira-utility`
- **IAM Role**: `github-to-jira-utility-role`
- **IAM Policy**: `github-to-jira-utility-role-secrets-policy`
- **EventBridge Rule**: `github-jira-utility-daily-run`
- **CloudWatch Log Group**: `/aws/lambda/github-to-jira-utility`


## Re-deploying

To update the Lambda code or configuration, just run the playbook again:

```bash
ansible-playbook deploy.yml -e secret_name=cloud_team_jira_login
```
