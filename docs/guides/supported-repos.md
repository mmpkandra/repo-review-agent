# Supported Repository Types

RunBook-AI automatically detects the type of repository and generates appropriate documentation.

## Application Repositories

Supports all major languages and frameworks:

- **Python** — FastAPI, Django, Flask
- **JavaScript / TypeScript** — React, Node.js, Express
- **Go, Rust, Java, Ruby, PHP**

## Infrastructure Repositories

RunBook-AI detects IaC tooling and generates infrastructure-specific documentation:

| IaC Tool | Detection | Generated Docs |
|----------|-----------|----------------|
| **Terraform** | `.tf` files, `main.tf`, `variables.tf` | Module architecture, variable reference, state management |
| **Ansible** | `playbook.yml`, `site.yml`, `ansible.cfg` | Role dependencies, inventory structure, execution guides |
| **Helm** | `Chart.yaml`, `values.yaml` | Chart structure, values reference, upgrade procedures |
| **Kustomize** | `kustomization.yaml` | Base/overlay structure, patch documentation |
| **Pulumi** | `Pulumi.yaml` | Stack configuration, resource documentation |
| **CloudFormation** | `.template` files, `cloudformation/` dirs | Stack parameters, outputs, nested stacks |
| **Kubernetes** | K8s manifests (YAML) | Resource documentation, deployment procedures |

## CI/CD Pipelines

| Platform | Detection | Extracted Info |
|----------|-----------|----------------|
| **GitHub Actions** | `.github/workflows/*.yml` | Workflow name, triggers, jobs, secrets, environments |
| **GitLab CI** | `.gitlab-ci.yml` | Stages, jobs, variables, environments |
| **Jenkins** | `Jenkinsfile` | Pipeline stages, credentials, agents |
| **CircleCI** | `.circleci/config.yml` | Jobs, workflows, orbs |

CI/CD information is included in:

- **Quality & Validation Guide** — Pipeline overview, quality gates, required checks
- **Deployment Runbook** — Automated deployment flow, environment promotion, rollback procedures
- **Developer Workflows** — Code ownership, issue/PR templates, branch strategies, release process

## GitHub Repository Configuration

RunBook-AI parses the full `.github/` folder:

| Config | File | What's Extracted |
|--------|------|------------------|
| **CODEOWNERS** | `CODEOWNERS` | Ownership rules (path → team) |
| **Dependabot** | `dependabot.yml` | Enabled ecosystems (npm, pip, docker) |
| **Issue Templates** | `ISSUE_TEMPLATE/` | Bug report, feature request templates |
| **PR Template** | `PULL_REQUEST_TEMPLATE.md` | Whether a PR template exists |
| **Custom Actions** | `.github/actions/` | Reusable composite actions |
| **Reusable Workflows** | Workflows with `workflow_call` | Shared CI/CD workflows |
| **Release Drafter** | `release-drafter.yml` | Automated release notes |
| **Funding** | `FUNDING.yml` | Sponsorship platforms |
| **Branch Protection** | Inferred from workflows | Protected branches (main, develop) |
