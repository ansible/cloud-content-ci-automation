# GitHub → Jira Lambda

Syncs GitHub issues labeled `jira` to ACA Jira. The function scans a fixed set of cloud-content repositories for issues with the `jira` label, checks which ones do not yet have a corresponding ACA issue (by matching the GitHub URL in existing Jira issue descriptions), and for each creates an ACA Bug with summary, description, labels, and components (e.g. cloud-content, Public Cloud / Container Native by repo). New issues are then transitioned to Backlog.

| Runtime   | Architecture |
|----------|--------------|
| Python 3.14 | arm64       |

## Configuration

The function runs in the cloud team AWS account with the following in place:

| Component | Value |
|-----------|--------|
| **Region** | `us-east-2` |
| **IAM role** | `github-to-jira-utility-role-*` (execution role for the function) |
| **Function name** | `github-to-jira-utility` |
| **Handler** | `handler.lambda_handler` |
| **Secrets Manager** | Secret `cloud_team_jira_login` (Jira + GitHub credentials) |
| **Environment** | `GITHUB_JIRA_SECRET_ID` set to the secret name or ARN for config lookup |

## How to run

### 1. Build the deployment package (Python 3.14, arm64)

From this directory (`tools/github-to-jira-utility/lambda/`):

```bash
./build-lambda.sh
```

This produces `deploy.zip`. The script uses `public.ecr.aws/lambda/python:3.14` and builds for **linux/arm64** (see `build-lambda.sh`). If your Lambda is configured for **amd64**, use `--platform linux/amd64` in the script or build on an amd64 host and zip as in the script’s fallback.

### 2. Update the Lambda code (when you change handler or dependencies)

```bash
aws lambda update-function-code \
  --function-name github-to-jira-utility \
  --zip-file fileb://deploy.zip \
  --region us-east-2
```

Or upload `deploy.zip` in the AWS Lambda console (Function code → Upload from → .zip file).

### 3. Invoke the Lambda

**One-off test (e.g. from AWS Console or CLI):**

```bash
aws lambda invoke \
  --function-name github-to-jira-utility \
  --region us-east-2 \
  --payload '{}' \
  response.json && cat response.json
```

Or use the AWS Console: open the function `github-to-jira-utility`, create a test event (e.g. `{}`), and run it.

**Scheduled runs:** An Amazon EventBridge schedule can run this Lambda on a schedule (e.g. daily). In the cloud team account there is a schedule named **`github-jira-utility-daily-run`**; it is currently **disabled**. Enable it in the EventBridge console (or via CLI) to run the sync on schedule.

## Secret

The secret referenced by `GITHUB_JIRA_SECRET_ID` must be JSON. The handler accepts either naming convention:

| Key (preferred) | Alternative | Purpose |
|----------------|-------------|---------|
| `cloud_team_jira_bot_token` | `jira_token` | Jira API token |
| `cloud_team_jira_server` | `jira_server` | Jira base URL (e.g. `https://issues.redhat.com`) |
| `cloud_team_gh_token` | `gh_token` | GitHub PAT with `repo` scope |

## Response

The handler returns JSON: `created` (number of new issues) and `issues` (list of `{ "key": "ACA-XXXX", "url": "<github issue url>" }`).
