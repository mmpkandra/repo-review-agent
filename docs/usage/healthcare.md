# Healthcare Mode (HIPAA Compliance)

RunBook-AI includes a healthcare mode that scans for PHI/PII before sending data to external AI services, enabling HIPAA-compliant documentation generation.

## Enable Healthcare Mode

```bash
# Scan for PHI/PII and BLOCK AI if found
repo-intel /path/to/your/repo --healthcare --output-docs ./docs

# Compliance scan with warnings only (doesn't block AI)
repo-intel /path/to/your/repo --compliance-scan --output-docs ./docs

# Thorough scan (all patterns including informational)
repo-intel /path/to/your/repo --healthcare --compliance-level thorough --output-docs ./docs
```

!!! danger "Force AI Override"
    You can override compliance blocking with `--force-ai`, but this is **strongly discouraged** in production environments with real patient data.

## How It Works

When `--healthcare` is enabled:

1. The compliance scanner runs against the entire codebase.
2. If **Critical** or **High** severity findings are detected, AI refinement is **automatically blocked**.
3. Heuristic-only documentation is still generated.
4. A `COMPLIANCE_REPORT.md` is written with full findings.

When `--compliance-scan` is used instead:

1. The scanner runs and a `COMPLIANCE_REPORT.md` is generated.
2. AI refinement proceeds regardless of findings.
3. Warnings are printed to the console.

## Scan Levels

| Level | What's Scanned | Use Case |
|-------|----------------|----------|
| `quick` | Critical patterns only | Fast CI/CD checks |
| `standard` | Critical + High (default) | Regular development |
| `thorough` | All patterns including info | Pre-audit, compliance review |

## Compliance Report

A `COMPLIANCE_REPORT.md` is generated containing:

- Executive summary with finding counts
- HIPAA/PCI compliance status
- Detailed findings with file locations and line numbers
- Remediation recommendations
- Checklist for fixes

!!! note
    `COMPLIANCE_REPORT.md` is listed in `.gitignore` by default because it may contain sensitive findings about your codebase.

## What Gets Detected

See the full [Compliance Scanning reference](../reference/compliance.md) for all detected categories and patterns.
