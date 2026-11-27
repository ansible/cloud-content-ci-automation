"""
GitHub Webhook to Slack notification handler for AWS Lambda.

Receives workflow_run events from GitHub, validates signature,
filters for certification.yml failures, and posts to Slack.
"""

import hashlib
import hmac
import json
import logging
import os
import urllib.request
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
WORKFLOW_NAME = os.environ.get("WORKFLOW_NAME", "Certification")


def verify_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature_header:
        return False

    expected_signature = (
        "sha256="
        + hmac.new(secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    )

    return hmac.compare_digest(expected_signature, signature_header)


def post_to_slack(webhook_url: str, message: dict[str, Any]) -> None:
    """Post message to Slack incoming webhook. Raises urllib.error.HTTPError on non-2xx."""
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(message).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=5).close()


def format_slack_message(
    workflow_run: dict[str, Any], repository: dict[str, Any]
) -> dict[str, Any]:
    """Format a rich Slack message for workflow failure."""
    workflow_name = workflow_run.get("name", "Unknown")
    conclusion = workflow_run.get("conclusion", "unknown")
    html_url = workflow_run.get("html_url", "")
    run_number = workflow_run.get("run_number", "N/A")
    head_branch = workflow_run.get("head_branch", "unknown")
    repo_name = repository.get("full_name", "unknown")

    fields = [
        ("Repository", repo_name),
        ("Branch", head_branch),
        ("Run Number", f"#{run_number}"),
        ("Conclusion", conclusion),
    ]

    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"❌ Workflow Failed: {workflow_name}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*{label}:*\n{value}"}
                    for label, value in fields
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Workflow Run",
                            "emoji": True,
                        },
                        "url": html_url,
                        "style": "danger",
                    }
                ],
            },
        ]
    }


def _response(status_code: int, **body: Any) -> dict[str, Any]:
    """Build a Lambda proxy response with a JSON body."""
    return {"statusCode": status_code, "body": json.dumps(body)}


def _skip_reason(workflow_run: dict[str, Any], target_workflow: str) -> str | None:
    """Return why this workflow_run should be ignored, or None to process it."""
    if workflow_run.get("name", "") != target_workflow:
        return f"Not {target_workflow} workflow, ignoring"
    if workflow_run.get("conclusion", "") != "failure":
        return "Workflow did not fail, ignoring"
    return None


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda handler for GitHub webhooks.

    Environment variables required:
    - GITHUB_WEBHOOK_SECRET: Secret for validating GitHub webhook signatures
    - SLACK_WEBHOOK_URL: Slack incoming webhook URL
    - WORKFLOW_NAME: Name of workflow to monitor (default: "Certification")
    """
    try:
        if not GITHUB_WEBHOOK_SECRET or not SLACK_WEBHOOK_URL:
            return _response(500, error="Missing required environment variables")

        headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
        signature_header = headers.get("x-hub-signature-256", "")
        body = event.get("body", "")
        body_bytes = body.encode("utf-8") if isinstance(body, str) else body

        if not verify_signature(body_bytes, signature_header, GITHUB_WEBHOOK_SECRET):
            return _response(401, error="Invalid signature")

        if headers.get("x-github-event", "") != "workflow_run":
            return _response(200, message="Not a workflow_run event, ignoring")

        payload = json.loads(body_bytes)
        workflow_run = payload.get("workflow_run", {})

        skip_reason = _skip_reason(workflow_run, WORKFLOW_NAME)
        if skip_reason:
            return _response(200, message=skip_reason)

        slack_message = format_slack_message(
            workflow_run, payload.get("repository", {})
        )
        post_to_slack(SLACK_WEBHOOK_URL, slack_message)

        logger.info(
            "Notification sent for %s run #%s",
            workflow_run.get("name", ""),
            workflow_run.get("run_number", "N/A"),
        )
        return _response(200, message="Notification sent to Slack")

    except Exception:
        logger.exception("Error processing webhook")
        return _response(500, error="Internal error processing webhook")
