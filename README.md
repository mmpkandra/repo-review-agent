# RunBook-AI

**Intelligent Repository Documentation Generator with Healthcare Compliance**

RunBook-AI analyzes any codebase and automatically generates documentation including RunBooks, Architecture Guides, Configuration Guides, and more. It includes built-in compliance scanning for PHI, PII, credentials, and secrets.

## Features

- **Deep Codebase Analysis**: Scans all files, extracts classes, functions, dependencies, environment variables, API endpoints, and scripts
- **AI-Powered Refinement**: Uses LLMs (OpenAI/AWS Bedrock) to generate professional prose, working code examples, and architecture diagrams
- **Multiple Output Formats**: Markdown (.md) for repositories, Word (.docx) for enterprise distribution
- **ISMS Compliance**: Word documents include cover pages, document control, version history, and proper classification
- **Healthcare Compliance**: Built-in PHI/PII detection with automatic AI blocking for HIPAA compliance
- **Secrets Detection**: 50+ patterns for credentials, API keys, and sensitive data
- **9 Document Types**: Repository Overview, Architecture Guide, Configuration Guide, Deployment Runbook, Operations Runbook, API Reference, Quality & Validation, Usage Patterns, Developer Workflows
- **Smart Document Splitting**: Automatically chunks large documents to avoid LLM token limits and content truncation


## Quick Start

### Installation

```bash
git clone https://github.com/your-org/RunBook-AI.git
cd RunBook-AI
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Basic Usage (No API Key Required)

```bash
# Generate documentation using heuristic extraction only
repo-intel /path/to/your/repo --output-docs ./docs

# Generate ALL 9 document types (regardless of what's detected)
repo-intel /path/to/your/repo --output-docs ./docs --all-docs

# Include Word documents
repo-intel /path/to/your/repo --output-docs ./docs --word
```

### Healthcare Mode (HIPAA Compliant)

```bash
# Scan for PHI/PII and block AI if found
repo-intel /path/to/your/repo --healthcare --output-docs ./docs

# Compliance scan without blocking AI (warnings only)
repo-intel /path/to/your/repo --compliance-scan --output-docs ./docs

# Thorough scan (all patterns including informational)
repo-intel /path/to/your/repo --healthcare --compliance-level thorough --output-docs ./docs
```

### Production Usage (With AI Refinement)

```bash
# Using OpenAI
export OPENAI_API_KEY=sk-...
repo-intel /path/to/your/repo \
  --output-docs ./docs \
  --use-ai \
  --word \
  --organization "Your Company" \
  --department "Engineering" \
  --classification "Confidential"
```

### AWS Bedrock Integration

RunBook-AI supports AWS Bedrock with multiple authentication methods. **AWS SSO is recommended** for enterprise use.

#### Option 1: AWS SSO (Recommended)

```bash
# Step 1: Login via AWS SSO
aws sso login --profile your-sso-profile

# Step 2: Run with the SSO profile
repo-intel /path/to/repo --use-ai --provider bedrock \
  --aws-profile your-sso-profile \
  --aws-region us-east-1 \
  --model claude-sonnet

# Or set the profile as environment variable
export AWS_PROFILE=your-sso-profile
export AWS_REGION=us-east-1
repo-intel /path/to/repo --use-ai --provider bedrock --model claude-sonnet
```

#### Option 2: AWS CLI Profile (credentials file)

```bash
repo-intel /path/to/repo --use-ai --provider bedrock \
  --aws-profile my-profile \
  --aws-region us-east-1 \
  --model claude-sonnet
```

#### Option 3: IAM Role Assumption (CI/CD, cross-account)

```bash
repo-intel /path/to/repo --use-ai --provider bedrock \
  --aws-role-arn arn:aws:iam::123456789:role/BedrockAccessRole \
  --aws-region us-east-1 \
  --model claude-sonnet
```

#### Option 4: Instance Profile (EC2, ECS, Lambda)

```bash
# Automatic - just ensure the instance/task role has Bedrock permissions
repo-intel /path/to/repo --use-ai --provider bedrock --aws-region us-east-1
```

#### Option 5: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
repo-intel /path/to/repo --use-ai --provider bedrock --model claude-sonnet
```

#### Supported Bedrock Models

| Alias | Full Model ID | Notes |
|-------|---------------|-------|
| `claude-3.7-sonnet` | `anthropic.claude-3-7-sonnet-20250219-v1:0` | **Recommended** - best balance of quality/speed |
| `claude-3.5-haiku` | `anthropic.claude-3-5-haiku-20241022-v1:0` | Fast, cost-effective |
| `claude-3-sonnet` | `anthropic.claude-3-sonnet-20240229-v1:0` | Stable, legacy |
| `claude-3-haiku` | `anthropic.claude-3-haiku-20240307-v1:0` | Fastest, legacy |
| `claude-sonnet` | `us.anthropic.claude-sonnet-4-5-*` | Claude 4.5 Sonnet (cross-region) |
| `claude-haiku` | `us.anthropic.claude-haiku-4-5-*` | Claude 4.5 Haiku (cross-region) |
| `claude-opus` | `us.anthropic.claude-opus-4-5-*` | Claude 4.5 Opus (cross-region) |
| `claude-4-sonnet` | `anthropic.claude-sonnet-4-5-*` | Claude 4.5 Sonnet (direct) |
| `claude-4-haiku` | `anthropic.claude-haiku-4-5-*` | Claude 4.5 Haiku (direct) |
| `titan-text` | `amazon.titan-text-premier-v1:0` | Amazon native |
| `llama3-70b` | `meta.llama3-70b-instruct-v1:0` | Open source |
| `mistral-large` | `mistral.mistral-large-2402-v1:0` | European |

**Note**: Use `claude-3.7-sonnet` for best results. Claude 4.x models with `us.` prefix use cross-region inference profiles.

#### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

## Compliance Scanning

RunBook-AI includes an option for comprehensive compliance scanner that detects sensitive data before it can be leaked to external AI services.

### What Gets Detected

| Category | Severity | Examples |
|----------|----------|----------|
| **Cloud Credentials** | Critical | AWS Access Keys, GCP API Keys, Azure SAS Tokens, Service Accounts |
| **API Keys** | Critical | OpenAI, Anthropic, Stripe, SendGrid, Twilio, Slack, GitHub PAT |
| **Database Secrets** | Critical | PostgreSQL, MySQL, MongoDB, Redis connection strings with passwords |
| **Private Keys** | Critical | RSA, PKCS8, OpenSSH, Encrypted private keys |
| **PHI Data** | Critical | SSN, Medical Record Numbers (MRN), Patient IDs |
| **PCI Data** | Critical | Credit Card Numbers, Bank Account Numbers |
| **Auth Tokens** | High | Bearer tokens, Basic Auth, JWT, OAuth tokens |
| **Passwords** | High | Hardcoded passwords, SSH passwords |
| **Encryption Keys** | High | AES keys, IV vectors, encryption secrets |
| **Infrastructure** | High | Private IPs, certificates, connection strings |

### Scan Levels

| Level | What's Scanned | Use Case |
|-------|----------------|----------|
| `quick` | Critical patterns only | Fast CI/CD checks |
| `standard` | Critical + High (default) | Regular development |
| `thorough` | All patterns including info | Pre-audit, compliance review |

### Compliance Report

When scanning is enabled, a `COMPLIANCE_REPORT.md` is generated with:
- Executive summary with finding counts
- HIPAA/PCI compliance status
- Detailed findings with file locations and line numbers
- Remediation recommendations
- Checklist for fixes

## CLI Options

| Option | Description |
|--------|-------------|
| `--output-docs DIR` | Output directory for generated docs |
| `--use-ai` | Enable AI refinement |
| `--provider` | AI provider: `openai` or `bedrock` |
| `--model` | Model ID or alias (see Bedrock models table) |
| `--aws-region` | AWS region for Bedrock (e.g., `us-east-1`) |
| `--aws-profile` | AWS CLI profile name for authentication |
| `--aws-role-arn` | IAM role ARN to assume for Bedrock access |
| `--word` | Generate Word documents |
| `--organization` | Organization name for Word docs |
| `--department` | Department name for Word docs |
| `--classification` | Document classification: `Public`, `Internal`, `Confidential`, `Restricted` |
| `--healthcare` | Enable healthcare mode (blocks AI if PHI/PII found) |
| `--compliance-scan` | Run compliance scan (warnings only, doesn't block AI) |
| `--compliance-level` | Scan depth: `quick`, `standard`, `thorough` |
| `--force-ai` | Force AI even if compliance issues found (NOT recommended) |
| `--all-docs` | Generate all 9 document types regardless of detection |
| `--json` | Output repository profile as JSON |

## Output Structure

```
docs/
├── REPOSITORY_OVERVIEW.md
├── ARCHITECTURE_GUIDE.md
├── CONFIGURATION_GUIDE.md
├── DEPLOYMENT_RUNBOOK.md
├── OPERATIONS_RUNBOOK.md
├── API_REFERENCE.md
├── QUALITY_AND_VALIDATION.md
├── USAGE_PATTERNS.md
├── DEVELOPER_WORKFLOWS.md
├── COMPLIANCE_REPORT.md          # When --healthcare or --compliance-scan
└── word/
    ├── REPOSITORY_OVERVIEW.docx
    ├── ARCHITECTURE_GUIDE.docx
    └── ... (ISMS-compliant documents)
```

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

## Supported Repository Types

### Application Repositories
- Python (FastAPI, Django, Flask)
- JavaScript/TypeScript (React, Node.js, Express)
- Go, Rust, Java, Ruby, PHP

### Infrastructure Repositories
RunBook-AI automatically detects and generates appropriate documentation for:

| IaC Tool | Detection | Generated Docs |
|----------|-----------|----------------|
| **Terraform** | `.tf` files, `main.tf`, `variables.tf` | Module architecture, variable reference, state management |
| **Ansible** | `playbook.yml`, `site.yml`, `ansible.cfg` | Role dependencies, inventory structure, execution guides |
| **Helm** | `Chart.yaml`, `values.yaml` | Chart structure, values reference, upgrade procedures |
| **Kustomize** | `kustomization.yaml` | Base/overlay structure, patch documentation |
| **Pulumi** | `Pulumi.yaml` | Stack configuration, resource documentation |
| **CloudFormation** | `.template` files, `cloudformation/` dirs | Stack parameters, outputs, nested stacks |
| **Kubernetes** | K8s manifests (YAML) | Resource documentation, deployment procedures |

### CI/CD Pipelines
RunBook-AI extracts and documents CI/CD workflows:

| Platform | Detection | Extracted Info |
|----------|-----------|----------------|
| **GitHub Actions** | `.github/workflows/*.yml` | Workflow name, triggers, jobs, secrets, environments |
| **GitLab CI** | `.gitlab-ci.yml` | Stages, jobs, variables, environments |
| **Jenkins** | `Jenkinsfile` | Pipeline stages, credentials, agents |
| **CircleCI** | `.circleci/config.yml` | Jobs, workflows, orbs |

### GitHub Repository Configuration
Full `.github/` folder parsing:

| Config | File | What's Extracted |
|--------|------|------------------|
| **CODEOWNERS** | `CODEOWNERS` | Ownership rules (path -> team) |
| **Dependabot** | `dependabot.yml` | Enabled ecosystems (npm, pip, docker) |
| **Issue Templates** | `ISSUE_TEMPLATE/` | Bug report, feature request templates |
| **PR Template** | `PULL_REQUEST_TEMPLATE.md` | Whether PR template exists |
| **Custom Actions** | `.github/actions/` | Reusable composite actions |
| **Reusable Workflows** | Workflows with `workflow_call` | Shared CI/CD workflows |
| **Release Drafter** | `release-drafter.yml` | Automated release notes |
| **Funding** | `FUNDING.yml` | Sponsorship platforms |
| **Branch Protection** | Inferred from workflows | Protected branches (main, develop) |

The CI/CD and GitHub config is included in:
- **Quality & Validation Guide**: Pipeline overview, quality gates, required checks
- **Deployment Runbook**: Automated deployment flow, environment promotion, rollback procedures
- **Developer Workflows**: Code ownership, issue/PR templates, branch strategies, release process

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ANALYZER (Local)                         │
│              Scans ALL files in repository                  │
├─────────────────────────────────────────────────────────────┤
│ Extracts: dependencies, env vars, classes, functions,       │
│ API endpoints, scripts, entry points, directory structure   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  COMPLIANCE SCANNER                         │
│           Detects PHI, PII, credentials, secrets            │
├─────────────────────────────────────────────────────────────┤
│ 50+ patterns: AWS keys, API tokens, SSN, credit cards,      │
│ private keys, database URIs, passwords, encryption keys     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM REFINEMENT (Optional)                  │
│           Document-specific prompts + full context          │
├─────────────────────────────────────────────────────────────┤
│ Generates: professional prose, code examples,               │
│ architecture diagrams, troubleshooting guides               │
│ BLOCKED if PHI/PII detected in healthcare mode              │
│                                                             │
│ SMART SPLITTING: For large repos (>50k tokens), documents   │
│ are generated section-by-section to avoid truncation        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  QUALITY POST-PROCESSING                    │
├─────────────────────────────────────────────────────────────┤
│ - Removes raw data dumps and "Repository Evidence"          │
│ - Removes inapplicable sections (e.g., Terraform for apps)  │
│ - Cleans up formatting and duplicate content                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT GENERATION                         │
├─────────────────────────────────────────────────────────────┤
│ - Markdown files (.md) for Git repositories                 │
│ - Word documents (.docx) with ISMS compliance               │
│ - Compliance report with findings and remediation           │
└─────────────────────────────────────────────────────────────┘
```

## Document Quality Features

### Smart Document Splitting

For repositories with large context (>50k estimated tokens), RunBook-AI automatically:
1. **Splits each document into logical sections** based on document type
2. **Generates each section separately** with focused prompts and condensed context
3. **Merges sections** into a complete, coherent document

This ensures:
- No content truncation at LLM output limits
- Better quality for each section (focused generation)
- Complete coverage of all document sections

### Content Quality Assurance

Post-processing automatically:
- **Removes raw data dumps** ("Repository Evidence" sections, raw JSON)
- **Removes inapplicable sections** (e.g., Terraform docs for non-infra repos)
- **Cleans up formatting** (excessive blank lines, duplicate content)

## Project Structure

```
src/repo_intel_agent/
├── analyzer.py           # Deep codebase extraction
├── compliance_scanner.py # PHI/PII/credential detection
├── models.py             # Data structures
├── docgen.py             # Markdown generation
├── llm.py                # AI refinement (OpenAI/Bedrock)
├── word_generator.py     # ISMS-compliant Word docs
├── agent.py              # Orchestration
└── cli.py                # Command-line interface
```

## Cost Estimation

### OpenAI (GPT-4.1-mini)

| Repo Size | Files | Estimated Cost |
|-----------|-------|----------------|
| Small | ~100 | ~$0.02 |
| Medium | ~500 | ~$0.05 |
| Large | ~1000 | ~$0.08 |
| Very Large | ~5000 | ~$0.15 |

### AWS Bedrock

Bedrock pricing varies by model. With Claude Sonnet:
- Input: ~$0.003 per 1K tokens
- Output: ~$0.015 per 1K tokens
- Typical repo (500 files): ~$0.10-0.20

## Creating a Custom GPT

You can create a Custom GPT that uses this tool's output to answer questions about any repository.

### Steps

1. **Generate documentation** for your target repository:
   ```bash
   repo-intel /path/to/repo --output-docs ./docs --use-ai --json > repo-profile.json
   ```

2. **Go to ChatGPT** -> Explore GPTs -> Create

3. **Configure the GPT**:
   - **Name**: "RepoName Expert Assistant"
   - **Description**: "Expert assistant for the RepoName codebase"
   - **Instructions**: Use the generated docs as knowledge base

4. **Upload Knowledge Files**: All generated `.md` files and `repo-profile.json`

## Extending RunBook-AI

### Adding New Document Types

1. Add document type to `_infer_doc_needs()` in `analyzer.py`
2. Add template method to `docgen.py`
3. Add document-specific prompt to `DOC_PROMPTS` in `llm.py`

### Adding New Compliance Patterns

1. Add pattern to `CRITICAL_PATTERNS`, `HIGH_PATTERNS`, `MEDIUM_PATTERNS`, or `LOW_PATTERNS` in `compliance_scanner.py`
2. Format: `"pattern_name": (r"regex", "Description", "category", "Recommendation")`

## Requirements

- Python 3.10+
- Dependencies: `boto3`, `openai`, `python-docx`, `pyyaml`

## License

Apache 2.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request
