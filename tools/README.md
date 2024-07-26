# GitHub Workflows Setup for Cloud Collections

## Overview
GitHub Action Workflows are extensively used for Continuous Integration (CI) testing in cloud collections. Detailed information about the tests can be found in the [CI documentation](https://github.com/ansible-collections/cloud-content-handbook/tree/main/CI). Supported Python and Ansible versions can be found in the [collections' CI documentation](https://github.com/ansible-collections/amazon.aws/blob/main/CI.md).

## CI Configuration Tool
The CI Configuration Tool is designed to scaffold common GitHub Action workflows and tox-ansible configuration file in various cloud collection repositories. This tool serves as a centralized location to make modifications to workflows, such as changing workflow calls or test versions, ensuring consistency across all collection repositories.

## Usage

**1.** Clone the [cloud-content-ci repository](https://github.com/ansible/cloud-content-ci-automation).
   ```
   git clone https://github.com/ansible/cloud-content-ci-automation
   ```

**2.** Provide the collection root path and the collections to which the GitHub workflow needs to be added in the [vars file](https://github.com/ansible/cloud-content-ci-automation/blob/main/tools/vars/main.yaml).

**3.** To make changes to the workflows, edit the [workflow files](https://github.com/ansible/cloud-content-ci-automation/blob/main/tools/files). Submit a pull request (PR) in your fork for review.

**4.** To edit or add GitHub workflows to the collections, ensure the collections are on their latest main branch. Run the [configure_ci](https://github.com/ansible/cloud-content-ci-automation/blob/main/tools/configure_ci.yaml) playbook as follows
   ```
   ansible-playbook configure_ci.yaml
   ```

To specify a particular version of ansible-lint, you can supply the version as an argument as below. The default value is configured to 'v24.7.0'.

   ```
   ansible-playbook configure_ci.yaml -e "ansible_lint_version=v24.7.0"
   ```
   This action creates a branch in the repositories listed in the [vars file](https://github.com/ansible/cloud-content-ci-automation/blob/main/tools/vars/main.yaml) and adds `tests.yml` and `linters.yml` workflows to the `.github/workflows` directory of the collections.

**5.** Navigate to the local version of your collection repository and review the changes made by the tool. Add and commit the changes. Create a PR with these changes in the collections upstream repository and submit the PRs for review.
