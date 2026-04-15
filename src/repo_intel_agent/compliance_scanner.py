"""Healthcare compliance scanner for PHI/PII detection in source code."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .models import ComplianceFinding, ComplianceReport


class ComplianceScanner:
    """Scan repositories for PHI, PII, and credential exposure."""

    # CRITICAL: Data that should NEVER be in source code
    CRITICAL_PATTERNS = {
        # === PHI PATTERNS ===
        "ssn_formatted": (
            r"\b\d{3}-\d{2}-\d{4}\b",
            "Social Security Number (formatted)",
            "phi",
            "Remove SSN from code. Use secure storage with encryption at rest.",
        ),
        "ssn_unformatted": (
            r"\b\d{9}\b(?=.*(?:ssn|social))",
            "Social Security Number (unformatted)",
            "phi",
            "Remove SSN from code. Use secure storage with encryption at rest.",
        ),
        "mrn_pattern": (
            r"\b(?:mrn|medical.?record|patient.?id)[\s:=]+['\"]?[A-Z0-9]{6,12}['\"]?",
            "Medical Record Number",
            "phi",
            "Remove MRN from code. Reference by variable, not hardcoded value.",
        ),
        # === PCI/FINANCIAL ===
        "credit_card": (
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            "Credit Card Number",
            "pii",
            "Remove credit card data. Use tokenization service.",
        ),
        "bank_account": (
            r"\b(?:account[_\s]?(?:number|num|no))[\s:=]+['\"]?\d{8,17}['\"]?",
            "Bank Account Number",
            "pii",
            "Remove bank account data. Use secure payment processor.",
        ),
        # === AWS CREDENTIALS ===
        "aws_access_key": (
            r"(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}",
            "AWS Access Key ID",
            "credential",
            "Remove AWS credentials. Use IAM roles or AWS Secrets Manager.",
        ),
        "aws_secret_key": (
            r"(?:aws)?[_-]?secret[_-]?(?:access)?[_-]?key[\s]*[=:][\s]*['\"][A-Za-z0-9/+=]{40}['\"]",
            "AWS Secret Access Key",
            "credential",
            "Remove AWS credentials. Use IAM roles or AWS Secrets Manager.",
        ),
        # === GCP CREDENTIALS ===
        "gcp_api_key": (
            r"AIza[0-9A-Za-z\-_]{35}",
            "Google Cloud API Key",
            "credential",
            "Remove GCP credentials. Use service accounts.",
        ),
        "gcp_service_account": (
            r'"type":\s*"service_account"',
            "GCP Service Account JSON",
            "credential",
            "Move service account JSON to secure secrets manager.",
        ),
        # === AZURE CREDENTIALS ===
        "azure_connection_string": (
            r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}",
            "Azure Storage Connection String",
            "credential",
            "Move to Azure Key Vault or environment variables.",
        ),
        "azure_sas_token": (
            r"sv=\d{4}-\d{2}-\d{2}&s[a-z]=[^&]+&sig=[A-Za-z0-9%]+",
            "Azure SAS Token",
            "credential",
            "Generate SAS tokens dynamically, don't hardcode.",
        ),
        # === GENERIC API KEYS ===
        "api_key_value": (
            r"(?:api[_-]?key|apikey|secret[_-]?key|auth[_-]?token)[\s]*[=:][\s]*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            "Hardcoded API Key/Secret",
            "credential",
            "Move to environment variable or secrets manager.",
        ),
        "bearer_token": (
            r"['\"]Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+['\"]",
            "Hardcoded Bearer Token",
            "credential",
            "Generate tokens dynamically, don't hardcode.",
        ),
        # === PRIVATE KEYS ===
        "private_key": (
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            "Private Key",
            "credential",
            "Remove private keys from code. Use secure key management.",
        ),
        "private_key_pkcs8": (
            r"-----BEGIN PRIVATE KEY-----",
            "PKCS8 Private Key",
            "credential",
            "Remove private keys from code. Use secure key management.",
        ),
        "private_key_encrypted": (
            r"-----BEGIN ENCRYPTED PRIVATE KEY-----",
            "Encrypted Private Key",
            "credential",
            "Move encrypted keys to secure key management.",
        ),
        # === OAUTH/AUTH TOKENS ===
        "github_token": (
            r"gh[pousr]_[A-Za-z0-9_]{36,}",
            "GitHub Personal Access Token",
            "credential",
            "Use GitHub Apps or GITHUB_TOKEN in CI. Rotate immediately.",
        ),
        "github_oauth": (
            r"gho_[A-Za-z0-9]{36}",
            "GitHub OAuth Token",
            "credential",
            "Remove OAuth token. Use proper OAuth flow.",
        ),
        "gitlab_token": (
            r"glpat-[A-Za-z0-9\-]{20,}",
            "GitLab Personal Access Token",
            "credential",
            "Use CI/CD variables or GitLab managed tokens.",
        ),
        "slack_token": (
            r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
            "Slack Token",
            "credential",
            "Move to environment variable. Rotate token immediately.",
        ),
        "slack_webhook": (
            r"https://hooks\.slack\.com/services/T[A-Z0-9]{8}/B[A-Z0-9]{8}/[a-zA-Z0-9]{24}",
            "Slack Webhook URL",
            "credential",
            "Move webhook URL to environment variable.",
        ),
        # === DATABASE SECRETS ===
        "postgres_uri": (
            r"postgres(?:ql)?://[^:]+:[^@]+@[^\s'\"]+",
            "PostgreSQL Connection URI with Password",
            "credential",
            "Use environment variables for database credentials.",
        ),
        "mysql_uri": (
            r"mysql://[^:]+:[^@]+@[^\s'\"]+",
            "MySQL Connection URI with Password",
            "credential",
            "Use environment variables for database credentials.",
        ),
        "mongodb_uri": (
            r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^\s'\"]+",
            "MongoDB Connection URI with Password",
            "credential",
            "Use environment variables for database credentials.",
        ),
        "redis_uri": (
            r"redis://[^:]*:[^@]+@[^\s'\"]+",
            "Redis Connection URI with Password",
            "credential",
            "Use environment variables for database credentials.",
        ),
        # === MESSAGING/QUEUE SECRETS ===
        "amqp_uri": (
            r"amqps?://[^:]+:[^@]+@[^\s'\"]+",
            "AMQP/RabbitMQ URI with Password",
            "credential",
            "Use environment variables for message queue credentials.",
        ),
        # === PAYMENT PROCESSORS ===
        "stripe_secret": (
            r"sk_live_[0-9a-zA-Z]{24,}",
            "Stripe Secret Key (Live)",
            "credential",
            "CRITICAL: Rotate immediately. Use environment variables.",
        ),
        "stripe_restricted": (
            r"rk_live_[0-9a-zA-Z]{24,}",
            "Stripe Restricted Key (Live)",
            "credential",
            "Rotate immediately. Use environment variables.",
        ),
        "paypal_client": (
            r"(?:paypal[_-]?(?:client[_-]?)?(?:id|secret))[\s:=]+['\"][A-Za-z0-9\-]{20,}['\"]",
            "PayPal Credentials",
            "credential",
            "Use environment variables for payment credentials.",
        ),
        # === COMMUNICATION SERVICES ===
        "twilio_key": (
            r"SK[0-9a-fA-F]{32}",
            "Twilio API Key",
            "credential",
            "Move to environment variable or secrets manager.",
        ),
        "sendgrid_key": (
            r"SG\.[A-Za-z0-9\-_]{22}\.[A-Za-z0-9\-_]{43}",
            "SendGrid API Key",
            "credential",
            "Move to environment variable or secrets manager.",
        ),
        "mailgun_key": (
            r"key-[0-9a-zA-Z]{32}",
            "Mailgun API Key",
            "credential",
            "Move to environment variable or secrets manager.",
        ),
        # === AI/ML SERVICES ===
        "openai_key": (
            r"sk-(?:proj)?[A-Za-z0-9\-]{32,}",
            "OpenAI API Key",
            "credential",
            "Move to environment variable. Rotate immediately.",
        ),
        "anthropic_key": (
            r"sk-ant-[A-Za-z0-9\-]{40,}",
            "Anthropic API Key",
            "credential",
            "Move to environment variable. Rotate immediately.",
        ),
        "huggingface_token": (
            r"hf_[A-Za-z0-9]{34}",
            "HuggingFace Token",
            "credential",
            "Move to environment variable.",
        ),
    }

    # HIGH: Strong indicators of PHI/PII that need review
    HIGH_PATTERNS = {
        # === PHI PATTERNS ===
        "patient_data_var": (
            r"\b(?:patient[_\s]?(?:name|dob|ssn|address|phone|email|diagnosis|medication))\s*[=:]",
            "Patient Data Variable Assignment",
            "phi",
            "Ensure this is not hardcoded PHI. Use secure data access patterns.",
        ),
        "health_record_literal": (
            r"['\"](?:diagnosis|prescription|treatment|medical[_\s]?history|health[_\s]?record)['\"][\s]*:",
            "Health Record Field",
            "phi",
            "Review for hardcoded PHI. Use data models, not literals.",
        ),
        "dob_pattern": (
            r"\b(?:dob|date[_\s]?of[_\s]?birth|birthdate)[\s]*[=:][\s]*['\"]?\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            "Date of Birth with Value",
            "phi",
            "Remove hardcoded DOB. Use parameterized queries.",
        ),
        # === CREDENTIALS ===
        "password_literal": (
            r"(?:password|passwd|pwd)[\s]*[=:][\s]*['\"][^'\"]{8,}['\"]",
            "Hardcoded Password",
            "credential",
            "Remove hardcoded password. Use environment variables or secrets manager.",
        ),
        "secret_assignment": (
            r"(?:secret|token|credential|auth_key)[\s]*[=:][\s]*['\"][^'\"]{16,}['\"]",
            "Hardcoded Secret/Token",
            "credential",
            "Move secrets to environment variables or secrets manager.",
        ),
        "basic_auth": (
            r"(?:basic|authorization)[\s:=]+['\"](?:Basic\s+)?[A-Za-z0-9+/=]{20,}['\"]",
            "Basic Auth Credentials",
            "credential",
            "Remove hardcoded auth. Use secure credential storage.",
        ),
        # === ENCRYPTION KEYS ===
        "encryption_key": (
            r"(?:encryption[_\s]?key|aes[_\s]?key|secret[_\s]?key)[\s]*[=:][\s]*['\"][A-Fa-f0-9]{32,}['\"]",
            "Hardcoded Encryption Key",
            "credential",
            "Use key management service (KMS) for encryption keys.",
        ),
        "iv_vector": (
            r"(?:iv|initialization[_\s]?vector)[\s]*[=:][\s]*['\"][A-Fa-f0-9]{16,}['\"]",
            "Hardcoded IV/Nonce",
            "credential",
            "Generate IV dynamically, never reuse.",
        ),
        # === INFRASTRUCTURE ===
        "ssh_password": (
            r"(?:ssh[_\s]?(?:pass(?:word)?|pwd))[\s]*[=:][\s]*['\"][^'\"]+['\"]",
            "SSH Password",
            "credential",
            "Use SSH keys instead of passwords.",
        ),
        "private_ip_hardcoded": (
            r"['\"](?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})['\"]",
            "Hardcoded Private IP Address",
            "secret",
            "Use DNS or service discovery instead of hardcoded IPs.",
        ),
        # === CERTIFICATES ===
        "certificate": (
            r"-----BEGIN CERTIFICATE-----",
            "Embedded Certificate",
            "secret",
            "Move certificates to secure certificate store.",
        ),
        # === API ENDPOINTS WITH KEYS ===
        "url_with_api_key": (
            r"https?://[^\s'\"]*[?&](?:api[_-]?key|token|secret|auth)=[A-Za-z0-9\-_]{16,}",
            "URL with Embedded API Key",
            "credential",
            "Remove API key from URL. Use headers or environment variables.",
        ),
        # === CLOUD SPECIFIC ===
        "aws_session_token": (
            r"(?:aws[_-]?)?session[_-]?token[\s]*[=:][\s]*['\"][A-Za-z0-9/+=]{100,}['\"]",
            "AWS Session Token",
            "credential",
            "Session tokens should be temporary and not stored in code.",
        ),
        "heroku_api_key": (
            r"(?:heroku[_-]?)?api[_-]?key[\s]*[=:][\s]*['\"][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}['\"]",
            "Heroku API Key",
            "credential",
            "Use Heroku CLI config or environment variables.",
        ),
        "digitalocean_token": (
            r"(?:do[_-]?)?(?:api[_-]?)?token[\s]*[=:][\s]*['\"][a-f0-9]{64}['\"]",
            "DigitalOcean Token",
            "credential",
            "Use environment variables or secrets manager.",
        ),
    }

    # MEDIUM: Patterns that may indicate PHI/PII handling
    MEDIUM_PATTERNS = {
        "phi_comment": (
            r"#.*\b(?:phi|hipaa|patient|medical|health.?record)\b",
            "PHI-related Comment",
            "phi",
            "Review code section for proper PHI handling.",
        ),
        "pii_field_names": (
            r"\b(?:first[_]?name|last[_]?name|full[_]?name|email|phone|address|zip[_]?code)[\s]*[=:]",
            "PII Field Assignment",
            "pii",
            "Ensure PII is not hardcoded. Use secure data handling.",
        ),
        "test_data_phi": (
            r"(?:test|mock|fake|dummy)[_\s]?(?:patient|ssn|mrn|dob)",
            "Test Data with PHI Fields",
            "phi",
            "Use synthetic test data generators, not realistic values.",
        ),
        "jwt_token": (
            r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "JWT Token",
            "credential",
            "Remove hardcoded JWT tokens. Generate dynamically.",
        ),
    }

    # LOW: Informational patterns
    LOW_PATTERNS = {
        "encryption_usage": (
            r"\b(?:encrypt|decrypt|aes|rsa|hash|bcrypt|argon2)\b",
            "Encryption/Hashing Usage",
            "info",
            "Verify proper encryption implementation.",
        ),
        "hipaa_mention": (
            r"\bhipaa\b",
            "HIPAA Mentioned",
            "info",
            "Review for HIPAA compliance requirements.",
        ),
        "audit_log": (
            r"\b(?:audit[_\s]?log|access[_\s]?log)\b",
            "Audit Logging",
            "info",
            "Ensure audit logging meets compliance requirements.",
        ),
    }

    # Files to always skip
    SKIP_FILES = {
        ".git", "node_modules", ".venv", "venv", "__pycache__",
        ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".lock", ".sum",
    }

    # Files that commonly have false positives
    FALSE_POSITIVE_FILES = {
        "package-lock.json", "yarn.lock", "poetry.lock",
        "go.sum", "Cargo.lock",
    }

    def __init__(self, scan_level: str = "standard") -> None:
        """
        Initialize scanner.

        Args:
            scan_level: "quick" (critical only), "standard" (critical+high),
                       "thorough" (all patterns)
        """
        self.scan_level = scan_level
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> dict:
        """Build pattern set based on scan level."""
        patterns = {"critical": self.CRITICAL_PATTERNS}

        if self.scan_level in ("standard", "thorough"):
            patterns["high"] = self.HIGH_PATTERNS

        if self.scan_level == "thorough":
            patterns["medium"] = self.MEDIUM_PATTERNS
            patterns["low"] = self.LOW_PATTERNS

        return patterns

    def scan_repository(self, root: Path) -> ComplianceReport:
        """Scan entire repository for compliance issues."""
        root = root.resolve()
        report = ComplianceReport(
            scan_timestamp=datetime.utcnow().isoformat(),
            repo_name=root.name,
            repo_path=str(root),
        )

        files_with_issues: set[str] = set()

        for file_path in self._iter_files(root):
            findings = self.scan_file(file_path, root)
            for finding in findings:
                files_with_issues.add(str(finding.file_path))
                self._add_finding(report, finding)
            report.total_files_scanned += 1

        report.files_with_findings = len(files_with_issues)
        self._assess_compliance(report)

        return report

    def scan_file(self, file_path: Path, root: Path) -> list[ComplianceFinding]:
        """Scan a single file for compliance issues."""
        findings: list[ComplianceFinding] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            return findings

        relative_path = file_path.relative_to(root)

        for line_num, line in enumerate(content.splitlines(), 1):
            # Skip comment-only lines for credential patterns
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                # Still check for PHI in comments
                line_findings = self._scan_line(
                    line, line_num, relative_path, comments_only=True
                )
            else:
                line_findings = self._scan_line(line, line_num, relative_path)

            findings.extend(line_findings)

        return findings

    def _scan_line(
        self,
        line: str,
        line_num: int,
        file_path: Path,
        comments_only: bool = False,
    ) -> list[ComplianceFinding]:
        """Scan a single line for patterns."""
        findings: list[ComplianceFinding] = []

        for severity, pattern_dict in self.patterns.items():
            for pattern_name, (regex, desc, category, recommendation) in pattern_dict.items():
                # Skip credential patterns in comments (likely documentation)
                if comments_only and category == "credential":
                    continue

                if re.search(regex, line, re.IGNORECASE):
                    # Create redacted sample
                    sample = self._redact_sample(line, regex)

                    findings.append(ComplianceFinding(
                        severity=severity,
                        category=category,
                        file_path=file_path,
                        line_number=line_num,
                        pattern_matched=pattern_name,
                        description=desc,
                        recommendation=recommendation,
                        data_sample=sample,
                    ))

        return findings

    def _redact_sample(self, line: str, pattern: str) -> str:
        """Redact sensitive data from sample while preserving context."""
        # Truncate line
        sample = line[:100] + ("..." if len(line) > 100 else "")
        # Redact the matched pattern
        sample = re.sub(pattern, "[REDACTED]", sample, flags=re.IGNORECASE)
        # Additional redaction for common sensitive patterns
        sample = re.sub(r"\d{3}-\d{2}-\d{4}", "[SSN]", sample)
        sample = re.sub(r"['\"][^'\"]{20,}['\"]", '"[REDACTED]"', sample)
        return sample.strip()

    def _iter_files(self, root: Path):
        """Iterate over scannable files."""
        for path in root.rglob("*"):
            if not path.is_file():
                continue

            # Skip by directory
            if any(skip in path.parts for skip in self.SKIP_FILES):
                continue

            # Skip by extension
            if path.suffix.lower() in self.SKIP_FILES:
                continue

            # Skip known false positive files
            if path.name in self.FALSE_POSITIVE_FILES:
                continue

            # Skip large files (likely binaries or data)
            try:
                if path.stat().st_size > 1_000_000:  # 1MB
                    continue
            except OSError:
                continue

            yield path

    def _add_finding(self, report: ComplianceReport, finding: ComplianceFinding) -> None:
        """Add finding to appropriate severity list."""
        if finding.severity == "critical":
            report.critical_findings.append(finding)
        elif finding.severity == "high":
            report.high_findings.append(finding)
        elif finding.severity == "medium":
            report.medium_findings.append(finding)
        else:
            report.low_findings.append(finding)

    def _assess_compliance(self, report: ComplianceReport) -> None:
        """Assess overall compliance status."""
        # Check HIPAA compliance
        phi_findings = [
            f for f in (report.critical_findings + report.high_findings)
            if f.category == "phi"
        ]
        if phi_findings:
            report.hipaa_compliant = False

        # Check PCI compliance
        pci_findings = [
            f for f in (report.critical_findings + report.high_findings)
            if f.category == "pii" and "credit" in f.description.lower()
        ]
        if pci_findings:
            report.pci_compliant = False

        # Check if safe for AI
        if report.critical_findings or report.high_findings:
            report.ai_safe = False
            categories = set(
                f.category for f in report.critical_findings + report.high_findings
            )
            report.ai_blocked_reason = (
                f"Repository contains {', '.join(categories)} data. "
                "AI refinement blocked to prevent data exposure."
            )

    def scan_content(self, content: str, source: str = "unknown") -> list[ComplianceFinding]:
        """Scan arbitrary content (for checking before AI calls)."""
        findings: list[ComplianceFinding] = []
        for line_num, line in enumerate(content.splitlines(), 1):
            line_findings = self._scan_line(line, line_num, Path(source))
            findings.extend(line_findings)
        return findings
