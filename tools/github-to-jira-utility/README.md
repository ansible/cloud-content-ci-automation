# GitHub-to-Jira Utility

Automated AWS Lambda function that syncs GitHub issues labeled `jira` to the ACA Jira project.

## What It Does

This Lambda function scans cloud-content repositories for issues with the `jira` label, identifies which ones don't yet have a corresponding ACA issue, and automatically creates Jira bugs with:

- Summary and description from GitHub issue
- Appropriate labels and components
- Automatic transition to Backlog status
- Link back to the original GitHub issue

The function is designed to run on a schedule (e.g., daily) to keep Jira and GitHub in sync.

## Deployment Options

Choose the deployment method that best fits your workflow:

### Option 1: Automated Deployment with Ansible (Recommended)

**One-command deployment with complete infrastructure setup**

The Ansible playbook automates everything: Lambda deployment, IAM roles, EventBridge scheduling, and CloudWatch Logs configuration.

**[See Ansible Deployment Guide](ansible/README.md)**

Quick start:
```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
ansible-playbook deploy.yml -e secret_name=cloud_team_jira_login
```

### Option 2: Manual Lambda Deployment

**For manual control or custom AWS configurations**

Step-by-step instructions for building and deploying the Lambda function manually using AWS CLI or Console.

**[See Lambda Manual Deployment Guide](lambda/README.md)**

## Directory Structure

```
.
├── ansible/              # Automated deployment with Ansible
│   ├── deploy.yml       # Main playbook
│   ├── requirements.yml # Ansible collections
│   └── README.md        # Deployment guide
└── lambda/              # Lambda function code
    ├── handler.py       # Function handler
    ├── requirements.txt # Python dependencies
    ├── build-lambda.sh  # Build script
    ├── create_deployment_zip.py  # Used by build script to create deploy.zip
    └── README.md        # Manual deployment guide
```

## Prerequisites

### For Ansible Deployment
- Ansible >= 2.15
- AWS CLI with configured credentials
- Docker or Podman (for building Lambda package)

### For Manual Deployment
- AWS CLI or Console access
- Docker or Podman (for building Lambda package)

### For Both Options
- AWS Secrets Manager secret with credentials:
  - `cloud_team_jira_bot_token` - Jira API token
  - `cloud_team_jira_server` - Jira server URL (e.g., `https://issues.redhat.com`)
  - `cloud_team_gh_token` - GitHub Personal Access Token with `repo` scope
