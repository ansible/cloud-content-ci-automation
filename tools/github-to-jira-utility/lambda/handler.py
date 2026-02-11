#!/usr/bin/env python3
#
# Simplified BSD License https://opensource.org/licenses/BSD-2-Clause)
#
# Lambda: config from AWS Secrets Manager (GITHUB_JIRA_SECRET_ID). Keys: jira_token, jira_server, gh_token.
#

import json
import logging
import os

import boto3
from jira import JIRA
from github import Github

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CLOUD_REPOS = [
    "ansible-collections/amazon.aws",
    "ansible-collections/kubernetes.core",
    "ansible-collections/amazon.cloud",
    "ansible-collections/cloud.terraform",
    "ansible-collections/cloud.common",
    "ansible-collections/community.aws",
    "ansible-collections/community.okd",
    "redhat-cop/cloud.aws_ops",
    "redhat-cop/cloud.aws_troubleshooting",
    "redhat-cop/cloud.gcp_ops",
    "redhat-cop/cloud.terraform_ops",
    "ansible/terraform-provider-aap",
    "ansible/terraform-provider-ansible",
]

dod_title = "Definition of Done"
dod_content = """
* Code Quality: Code adheres to team coding standards and is well-documented.
* Testing: All tests pass successfully, and relevant tests are updated.
* Review and Approval: PR has been reviewed, and feedback has been addressed.
* Documentation: Relevant documentation has been updated (e.g., README, release notes).
* Functionality: Code meets requirements and works as expected without regressions.
* Merging: PR is up to date with the base branch and free of merge conflicts.
* Backporting: Relevant backport labels are added based on the nature of the fix, and backported PRs are approved and merged.
"""


def _normalize_config(raw: dict) -> dict:
    """Map secret keys to internal config. Supports:
    - cloud_team_* keys (e.g. cloud_team_jira_login secret):
      cloud_team_jira_bot_token, cloud_team_jira_server, cloud_team_gh_token (or gh_token)
    - legacy keys: jira_token, jira_server, gh_token
    """
    return {
        "jira_token": raw.get("cloud_team_jira_bot_token") or raw.get("jira_token"),
        "jira_server": raw.get("cloud_team_jira_server") or raw.get("jira_server"),
        "gh_token": raw.get("cloud_team_gh_token") or raw.get("gh_token"),
    }


def get_config_from_secrets(secret_id: str) -> dict:
    """Load config from AWS Secrets Manager. Secret must be JSON.
    Supported keys (either naming convention):
    - Jira: cloud_team_jira_bot_token / jira_token; cloud_team_jira_server / jira_server
    - GitHub: cloud_team_gh_token / gh_token
    """
    client = boto3.client("secretsmanager")
    resp = client.get_secret_value(SecretId=secret_id)
    secret = resp.get("SecretString")
    if not secret:
        raise ValueError("Secret has no SecretString")
    raw = json.loads(secret)
    return _normalize_config(raw)


def run_sync(config: dict) -> list:
    """Create Jira issues for GitHub issues with 'jira' label that don't already have one."""
    print("[run_sync] Connecting to GitHub and Jira...")
    g = Github(config["gh_token"])
    jiraconn = JIRA(
        token_auth=config["jira_token"],
        server=config["jira_server"],
    )
    print("[run_sync] Jira connected, fetching existing ACA issues with label=github...")

    jira_issues = jiraconn.search_issues(
        "project=ACA and labels=github", maxResults=1000
    )
    print("[run_sync] Found {} existing Jira issue(s) with label github".format(len(jira_issues)))

    # Components are resource objects
    prj_components = jiraconn.project_components(project="ACA")
    ctn_native_comp = pub_cloud_comp = priv_cloud_comp = None
    for comp in prj_components:
        if comp.name == "Container Native":
            ctn_native_comp = comp
        elif comp.name == "Public Cloud":
            pub_cloud_comp = comp
        elif comp.name == "Private Cloud":
            priv_cloud_comp = comp
        else:
            continue
    print("[run_sync] ACA components: Container Native={}, Public Cloud={}, Private Cloud={}".format(
        ctn_native_comp.name if ctn_native_comp else None,
        pub_cloud_comp.name if pub_cloud_comp else None,
        priv_cloud_comp.name if priv_cloud_comp else None,
    ))

    github_issues = []
    for repo_name in CLOUD_REPOS:
        repo = g.get_repo(repo_name)
        issues = list(repo.get_issues(labels=["jira"]))
        github_issues.extend(issues)
        print("[run_sync] Repo {}: {} issue(s) with label jira".format(repo_name, len(issues)))
    print("[run_sync] Total GitHub issues with label jira: {}".format(len(github_issues)))

    to_create = []
    for bug in github_issues:
        # If the Github URL does not appear in any github-labelled Jira issue descriptions, we will create a new Jira bug
        if not any(
            bug.html_url in (jira_obj.fields.description or "") for jira_obj in jira_issues
        ):
            to_create.append(bug)
    print("[run_sync] GitHub issues not yet in Jira (to_create): {}".format(len(to_create)))
    for bug in to_create:
        title_preview = (bug.title or "")[:50] + ("..." if len(bug.title or "") > 50 else "")
        print("[run_sync]   - {} #{}: {} | {}".format(bug.repository.name, bug.number, title_preview, bug.html_url))

    # Label and component by repo. Every issue gets cloud-content; AWS also gets Public Cloud, Kubernetes also gets Container Native.
    AWS_REPOS = ["amazon.aws", "community.aws", "cloud.aws_ops", "cloud.aws_troubleshooting"]
    GCP_REPOS = ["cloud.gcp_ops"]
    KUBERNETES_REPOS = ["kubernetes.core", "community.okd"]

    created = []
    for bug in to_create:
        repo_name = bug.repository.name
        if repo_name in AWS_REPOS:
            labels = ["github", "aws"]
            components = [{"name": "cloud-content"}, {"name": "Public Cloud"}]
        elif repo_name in GCP_REPOS:
            labels = ["github", "gcp"]
            components = [{"name": "cloud-content"}, {"name": "Public Cloud"}]
        elif repo_name in KUBERNETES_REPOS:
            labels = ["github", "kubernetes"]
            components = [{"name": "cloud-content"}, {"name": "Container Native"}]
        elif repo_name == "vmware.vmware_rest":
            labels = ["github", "vmware"]
            components = [{"name": "cloud-content"}, {"name": "Private Cloud"}]
        else:
            labels = ["github"]
            components = [{"name": "cloud-content"}]

        issue_template = {
            "project": "ACA",
            "summary": "[{0}/{1}] {2}".format(
                bug.repository.name, bug.number, bug.title
            ),
            "description": "This issue is created from the GitHub issue by github-to-jira-utility running in Lambda. \n {0} \n {1} \n h3. {2} \n {3}".format(
                bug.html_url, bug.body or "", dod_title, dod_content
            ),
            "issuetype": {"name": "Bug"},
            "labels": labels,
            "priority": {"name": "Undefined"},
            "components": components,
            "versions": [{"id": "12398634"}],
            "customfield_12319275": [
                {"value": "Cloud Content"}
            ],  # Workstream field
        }
        summary = issue_template["summary"]
        print("[run_sync] Creating Jira story: {} | from {}".format(summary, bug.html_url))
        issue = jiraconn.create_issue(fields=issue_template)
        print("[run_sync] Created Jira issue: {} (id={}) | {}".format(issue.key, issue.id, bug.html_url))
        logger.info("%s", issue.id)
        # Transition the issue from New to Backlog
        jiraconn.transition_issue(issue.id, "Backlog")
        created.append({"key": issue.key, "url": bug.html_url})

    print("[run_sync] Done. Created {} Jira issue(s).".format(len(created)))
    return created


def lambda_handler(event, context):
    """
    Lambda entry point.
    Config is read from AWS Secrets Manager.
    Set env var GITHUB_JIRA_SECRET_ID on the lambda function to the secret name/ARN (e.g. cloud_team_jira_login).
    """
    print("[lambda_handler] Starting GitHub->Jira sync...")
    secret_id = os.environ.get("GITHUB_JIRA_SECRET_ID")
    if not secret_id:
        raise ValueError("GITHUB_JIRA_SECRET_ID environment variable is required")
    print("[lambda_handler] Loading config from secret: {}".format(secret_id))

    config = get_config_from_secrets(secret_id)
    missing = [k for k in ("jira_token", "jira_server", "gh_token") if not config.get(k)]
    if missing:
        raise ValueError(
            "Secret must contain Jira and GitHub credentials. Missing: {}. "
            "For cloud_team_jira_login use: cloud_team_jira_bot_token, cloud_team_jira_server, "
            "and add cloud_team_gh_token or gh_token (GitHub PAT).".format(missing)
        )

    created = run_sync(config)
    print("[lambda_handler] Finished. Created {} issue(s): {}".format(len(created), [c["key"] for c in created]))
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"created": len(created), "issues": created},
            indent=2,
        ),
    }
