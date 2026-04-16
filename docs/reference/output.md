# Output Structure

## Generated Files

When you run `repo-intel`, the following files may be created in your output directory depending on what is detected (or all 9 if `--all-docs` is used):

```
docs/
├── REPOSITORY_OVERVIEW.md       # Executive summary, tech stack, purpose
├── ARCHITECTURE_GUIDE.md        # System design, components, data flows
├── CONFIGURATION_GUIDE.md       # Environment variables, config files
├── DEPLOYMENT_RUNBOOK.md        # Deployment steps, CI/CD, rollback
├── OPERATIONS_RUNBOOK.md        # Day-2 ops, monitoring, incident response
├── API_REFERENCE.md             # Endpoint catalog with request/response
├── QUALITY_AND_VALIDATION.md    # Testing strategy, quality gates
├── USAGE_PATTERNS.md            # Tutorials, how-tos, common patterns
├── DEVELOPER_WORKFLOWS.md       # Branching, PR process, conventions
├── COMPLIANCE_REPORT.md         # Only when --healthcare or --compliance-scan
└── word/
    ├── REPOSITORY_OVERVIEW.docx
    ├── ARCHITECTURE_GUIDE.docx
    └── ... (ISMS-compliant Word documents)
```

## Document Selection

RunBook-AI automatically selects which documents to generate based on what it detects in the repository:

- A repo with only Markdown and no code → `REPOSITORY_OVERVIEW.md`, `USAGE_PATTERNS.md`
- A Python FastAPI service → all API, deployment, and architecture docs
- A Terraform repo → architecture, deployment, and configuration docs

Use `--all-docs` to always generate all 9 document types.

## Word Document Features

Word documents generated with `--word` include ISMS-compliant formatting:

- **Cover page** with title, classification, date, and organization
- **Document control table** (author, reviewer, version)
- **Version history table**
- **Section headers** styled for enterprise distribution
- **Proper classification banners** (`Public`, `Internal`, `Confidential`, `Restricted`)

## What Gets Extracted

| Data Type | Method | Example |
|-----------|--------|---------|
| **Dependencies** | Parses pyproject.toml, package.json, requirements.txt | `openai`, `boto3`, `react` |
| **Environment Variables** | Scans .env.example + Python code | `OPENAI_API_KEY`, `DATABASE_URL` |
| **Classes & Functions** | Regex extraction from all code files | 866 classes, 2351 functions |
| **API Endpoints** | FastAPI/Flask decorator detection | `GET /api/users`, `POST /auth` |
| **Scripts** | Makefile targets, npm scripts | `make test`, `npm run build` |
| **Entry Points** | pyproject.toml, package.json bin | `repo-intel`, `python -m app` |
| **Directory Structure** | Full codebase mapping with summaries | Purpose of each directory |
| **IaC Tools** | Terraform, Ansible, Helm, Kustomize, Pulumi, CloudFormation | `terraform`, `ansible` |
| **CI/CD Workflows** | GitHub Actions, GitLab CI, Jenkins, CircleCI | Triggers, jobs, secrets, environments |
