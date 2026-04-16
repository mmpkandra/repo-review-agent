# Architecture

## System Overview

RunBook-AI is a pipeline of four local stages followed by optional AI refinement.

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

## Smart Document Splitting

For repositories with large context (>50k estimated tokens), RunBook-AI automatically:

1. **Splits each document into logical sections** based on document type
2. **Generates each section separately** with focused prompts and condensed context
3. **Merges sections** into a complete, coherent document

This ensures:

- No content truncation at LLM output limits
- Better quality for each section (focused generation)
- Complete coverage of all document sections

## Content Quality Assurance

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
