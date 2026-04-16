# RunBook-AI

**Intelligent Repository Documentation Generator with Healthcare Compliance**

RunBook-AI analyzes any codebase and automatically generates documentation including RunBooks, Architecture Guides, Configuration Guides, and more. It includes built-in compliance scanning for PHI, PII, credentials, and secrets.

## Features

<div class="grid cards" markdown>

- :material-magnify: **Deep Codebase Analysis**

    Scans all files, extracts classes, functions, dependencies, environment variables, API endpoints, and scripts.

- :material-robot: **AI-Powered Refinement**

    Uses LLMs (OpenAI/AWS Bedrock) to generate professional prose, working code examples, and architecture diagrams.

- :material-file-document-multiple: **Multiple Output Formats**

    Markdown (`.md`) for repositories, Word (`.docx`) for enterprise distribution.

- :material-shield-check: **ISMS Compliance**

    Word documents include cover pages, document control, version history, and proper classification.

- :material-hospital-box: **Healthcare Compliance**

    Built-in PHI/PII detection with automatic AI blocking for HIPAA compliance.

- :material-key-variant: **Secrets Detection**

    50+ patterns for credentials, API keys, and sensitive data.

- :material-file-tree: **9 Document Types**

    Repository Overview, Architecture Guide, Configuration Guide, Deployment Runbook, Operations Runbook, API Reference, Quality & Validation, Usage Patterns, Developer Workflows.

- :material-scissors-cutting: **Smart Document Splitting**

    Automatically chunks large documents to avoid LLM token limits and content truncation.

</div>

## Quick Links

<div class="grid cards" markdown>

- :material-rocket-launch: [**Get Started**](quickstart.md) — Install and generate your first docs in minutes
- :material-console: [**CLI Reference**](reference/cli.md) — All options and flags explained
- :material-shield-lock: [**Compliance Scanning**](reference/compliance.md) — PHI, PII, and secrets detection
- :material-hospital: [**Healthcare Mode**](usage/healthcare.md) — HIPAA-compliant document generation

</div>
