# Cloud Content CI Automation

A repository of tools that can be used to automate CI configurations/functionalities.

## Tools

- **[tools/github-to-jira-utility/](tools/github-to-jira-utility/)** — Syncs GitHub issues (with the `jira` label) to ACA Jira issues (e.g. via Lambda). See that folder's README for setup and usage.

## Actions

- **[.github/actions/security_check_directories/](.github/actions/security_check_directories/)** — Blocks PRs that add files to `.claude/` or `.vscode/` directories.
- **[.github/actions/cicd_change_detector/](.github/actions/cicd_change_detector/)** — Flags PRs that modify CI/CD configuration files with a label and security review checklist.
