# Basic Usage

## Generate Documentation Without AI

RunBook-AI can analyze any codebase and produce high-quality documentation without any API keys using heuristic extraction.

```bash
# Minimal — generates only the docs relevant to what's detected
repo-intel /path/to/your/repo --output-docs ./docs

# Force all 9 document types regardless of what's detected
repo-intel /path/to/your/repo --output-docs ./docs --all-docs

# Include Word (.docx) documents alongside Markdown
repo-intel /path/to/your/repo --output-docs ./docs --word
```

## Generate Documentation With AI Refinement

=== "OpenAI"

    ```bash
    export OPENAI_API_KEY=sk-...
    repo-intel /path/to/your/repo \
      --output-docs ./docs \
      --use-ai
    ```

=== "AWS Bedrock"

    ```bash
    repo-intel /path/to/your/repo \
      --output-docs ./docs \
      --use-ai \
      --provider bedrock \
      --aws-region us-east-1 \
      --model claude-3.7-sonnet
    ```

## Enterprise Word Documents

Word documents include ISMS-compliant cover pages, document control tables, and version history.

```bash
repo-intel /path/to/your/repo \
  --output-docs ./docs \
  --use-ai \
  --word \
  --organization "Acme Corp" \
  --department "Engineering" \
  --classification "Confidential"
```

Supported classification levels: `Public`, `Internal`, `Confidential`, `Restricted`.

## Export Repository Profile as JSON

```bash
repo-intel /path/to/your/repo --json > repo-profile.json
```

This exports the full extracted metadata — useful for downstream processing, Custom GPT knowledge files, or debugging what was detected.

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
