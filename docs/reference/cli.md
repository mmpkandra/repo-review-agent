# CLI Options

Full reference for all `repo-intel` command-line options.

## Usage

```
repo-intel <repo-path> [OPTIONS]
```

## Options

### Output

| Option | Description |
|--------|-------------|
| `--output-docs DIR` | Output directory for generated Markdown documents |
| `--word` | Also generate ISMS-compliant Word (`.docx`) documents |
| `--json` | Print the extracted repository profile as JSON to stdout |
| `--all-docs` | Generate all 9 document types regardless of what's detected |

### AI Refinement

| Option | Description |
|--------|-------------|
| `--use-ai` | Enable AI refinement of generated documents |
| `--provider` | AI provider: `openai` (default) or `bedrock` |
| `--model` | Model ID or alias — see [AWS Bedrock models](../usage/bedrock.md#supported-models) |

### AWS Bedrock Authentication

| Option | Description |
|--------|-------------|
| `--aws-region` | AWS region for Bedrock (e.g., `us-east-1`) |
| `--aws-profile` | AWS CLI profile name for authentication |
| `--aws-role-arn` | IAM role ARN to assume for Bedrock access |

### Word Document Metadata

| Option | Description |
|--------|-------------|
| `--organization` | Organization name for Word document headers |
| `--department` | Department name for Word document headers |
| `--classification` | Document classification: `Public`, `Internal`, `Confidential`, `Restricted` |

### Compliance & Healthcare

| Option | Description |
|--------|-------------|
| `--healthcare` | Enable healthcare mode — blocks AI if PHI/PII found |
| `--compliance-scan` | Run compliance scan with warnings only; does not block AI |
| `--compliance-level` | Scan depth: `quick`, `standard` (default), or `thorough` |
| `--force-ai` | Force AI even if compliance issues found (**not recommended**) |

## Examples

```bash
# Heuristic-only docs in ./docs
repo-intel /path/to/repo --output-docs ./docs

# All 9 docs + Word output with AI via OpenAI
repo-intel /path/to/repo \
  --output-docs ./docs \
  --use-ai \
  --all-docs \
  --word \
  --organization "Acme Corp" \
  --classification "Internal"

# Healthcare-compliant run with thorough scan
repo-intel /path/to/repo \
  --output-docs ./docs \
  --healthcare \
  --compliance-level thorough \
  --use-ai \
  --provider bedrock \
  --model claude-3.7-sonnet \
  --aws-region us-east-1

# Export JSON profile
repo-intel /path/to/repo --json > repo-profile.json
```
