# Installation & Quick Start

## Requirements

- Python 3.10+
- Dependencies: `boto3`, `openai`, `python-docx`, `pyyaml`

## Installation

```bash
git clone https://github.com/mmpkandra/repo-review-agent.git
cd repo-review-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Basic Usage (No API Key Required)

```bash
# Generate documentation using heuristic extraction only
repo-intel /path/to/your/repo --output-docs ./docs

# Generate ALL 9 document types (regardless of what's detected)
repo-intel /path/to/your/repo --output-docs ./docs --all-docs

# Include Word documents
repo-intel /path/to/your/repo --output-docs ./docs --word
```

## Production Usage (With AI Refinement)

=== "OpenAI"

    ```bash
    export OPENAI_API_KEY=sk-...
    repo-intel /path/to/your/repo \
      --output-docs ./docs \
      --use-ai \
      --word \
      --organization "Your Company" \
      --department "Engineering" \
      --classification "Confidential"
    ```

=== "AWS Bedrock"

    ```bash
    repo-intel /path/to/repo --use-ai --provider bedrock \
      --aws-profile your-sso-profile \
      --aws-region us-east-1 \
      --model claude-3.7-sonnet
    ```

See [AWS Bedrock Integration](usage/bedrock.md) for full authentication options and model details.

## What's Generated

After running, you'll find files like this in your output directory:

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
    └── ... (ISMS-compliant documents)
```

See [Output Structure](reference/output.md) for details on each document type.
