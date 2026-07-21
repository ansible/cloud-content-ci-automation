# CI/CD Change Detector

Detects when a PR modifies CI/CD configuration files and flags them for enhanced security review by adding a `ci-cd-change` label and posting a review checklist comment.

## Usage

```yaml
name: CI/CD Change Detection
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write

jobs:
  cicd-change-check:
    runs-on: ubuntu-latest
    steps:
      - name: Detect CI/CD changes
        uses: ansible/cloud-content-ci-automation/.github/actions/cicd_change_detector@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

> **Note:** The example above uses `@main`. For stricter supply-chain security, pin to a commit SHA (e.g., `@a1b2c3d`).

> **Note:** Ensure the workflow has `pull-requests: write` permission. In repositories with restricted `GITHUB_TOKEN` permissions, you may need to explicitly grant this in Settings → Actions → General → Workflow permissions.

## Inputs

| Name | Required | Description |
|------|----------|-------------|
| `github-token` | Yes | GitHub token with `pull-requests: write` permission |
| `label-name` | No | Optional label to add when CI/CD files are detected |

## Behavior

When CI/CD files are detected in a PR, the action:

1. Adds a `ci-cd-change` label to the PR (creates the label in the repo if it doesn't exist)
2. Posts a one-time security review checklist comment (skips if already posted)

 ## Detected Files and Patterns

  The following files and directories are flagged as CI/CD configuration:

  | Pattern | Description |
  |---------|-------------|
  | `.github/workflows/*.yml` / `.yaml` | GitHub Actions workflow definitions |
  | `.github/actions/**` | GitHub composite and custom actions |
  | `Makefile` / `makefile` / `GNUmakefile` | Build automation |
  | `tox.ini` | Python test automation |
  | `noxfile.py` | Python test automation |
  | `.zuul.yaml` / `.zuul.d/**` | Zuul CI configuration |
