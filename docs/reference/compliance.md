# Compliance Scanning

RunBook-AI includes a comprehensive compliance scanner that detects sensitive data before it can be leaked to external AI services.

## What Gets Detected

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

## Scan Levels

| Level | What's Scanned | Use Case |
|-------|----------------|----------|
| `quick` | Critical patterns only | Fast CI/CD checks |
| `standard` | Critical + High (default) | Regular development |
| `thorough` | All patterns including informational | Pre-audit, compliance review |

## Running a Scan

```bash
# Warnings only, AI still runs
repo-intel /path/to/repo --compliance-scan --output-docs ./docs

# Block AI if issues found (healthcare mode)
repo-intel /path/to/repo --healthcare --output-docs ./docs

# Thorough scan
repo-intel /path/to/repo --compliance-scan --compliance-level thorough --output-docs ./docs
```

## Compliance Report

When scanning is enabled, a `COMPLIANCE_REPORT.md` is generated containing:

- **Executive summary** with finding counts by severity
- **HIPAA/PCI compliance status**
- **Detailed findings** with file locations and line numbers
- **Remediation recommendations**
- **Fix checklist**

!!! warning
    `COMPLIANCE_REPORT.md` is listed in `.gitignore` by default because it may contain sensitive details about your codebase.

## Adding Custom Patterns

To extend the scanner with your own patterns, add entries to the appropriate dictionary in `compliance_scanner.py`:

```python
CRITICAL_PATTERNS = {
    "my_pattern": (
        r"regex_pattern_here",
        "Human-readable description",
        "category",
        "Remediation recommendation"
    ),
    ...
}
```

Available severity levels: `CRITICAL_PATTERNS`, `HIGH_PATTERNS`, `MEDIUM_PATTERNS`, `LOW_PATTERNS`.
