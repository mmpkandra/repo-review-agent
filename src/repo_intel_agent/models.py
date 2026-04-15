from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CodeSymbol:
    """A class or function with its description."""
    name: str
    symbol_type: str  # "class" or "function"
    docstring: str = ""  # First line of docstring
    signature: str = ""  # Parameters for functions, base classes for classes
    file_path: str = ""


@dataclass(slots=True)
class FileInsight:
    path: Path
    category: str
    language: str
    doc_signal: str
    size_bytes: int = 0
    is_entry_point: bool = False
    importance_score: float = 0.0  # 0-1 score for prioritizing context
    # Code structure extracted from the file (legacy - just names)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    # Enhanced: symbols with descriptions
    symbols: list["CodeSymbol"] = field(default_factory=list)


@dataclass(slots=True)
class DirectorySummary:
    """Summary of a directory's contents for LLM context."""
    path: str
    file_count: int
    languages: dict[str, int] = field(default_factory=dict)
    categories: dict[str, int] = field(default_factory=dict)
    key_files: list[str] = field(default_factory=list)
    all_classes: list[str] = field(default_factory=list)
    all_functions: list[str] = field(default_factory=list)
    description: str = ""
    # Enhanced: symbols with descriptions
    symbols: list["CodeSymbol"] = field(default_factory=list)


@dataclass(slots=True)
class Dependency:
    name: str
    version: str | None = None
    dev_only: bool = False
    source: str = ""  # e.g., "pyproject.toml", "package.json"


@dataclass(slots=True)
class EnvVariable:
    name: str
    source_file: Path | None = None
    required: bool = True
    description: str = ""
    default_value: str | None = None


@dataclass(slots=True)
class EntryPoint:
    name: str
    path: Path
    entry_type: str  # "cli", "web", "script", "module", "api"
    command: str | None = None  # e.g., "python -m repo_intel_agent"
    description: str = ""


@dataclass(slots=True)
class ConfigFile:
    path: Path
    config_type: str  # "env", "yaml", "json", "toml", "ini"
    purpose: str = ""
    keys: list[str] = field(default_factory=list)


@dataclass(slots=True)
class APIEndpoint:
    path: str
    method: str
    source_file: Path | None = None
    description: str = ""


@dataclass(slots=True)
class Script:
    name: str
    command: str
    source: str  # e.g., "package.json scripts", "Makefile"
    description: str = ""


@dataclass(slots=True)
class CIWorkflow:
    """CI/CD workflow (GitHub Actions, GitLab CI, etc.)."""
    name: str
    file_path: Path
    platform: str  # "github-actions", "gitlab-ci", "jenkins", "circleci"
    triggers: list[str] = field(default_factory=list)  # push, pull_request, schedule, etc.
    jobs: list[str] = field(default_factory=list)  # Job names
    environments: list[str] = field(default_factory=list)  # deploy targets
    secrets_used: list[str] = field(default_factory=list)  # secrets referenced
    description: str = ""


@dataclass(slots=True)
class GitHubConfig:
    """GitHub repository configuration from .github/ folder."""
    # Code ownership
    codeowners: list[str] = field(default_factory=list)  # ownership rules

    # Dependabot
    dependabot_enabled: bool = False
    dependabot_ecosystems: list[str] = field(default_factory=list)  # npm, pip, docker, etc.

    # Templates
    issue_templates: list[str] = field(default_factory=list)
    pr_template: bool = False

    # Branch protection (inferred from workflows)
    protected_branches: list[str] = field(default_factory=list)
    required_checks: list[str] = field(default_factory=list)

    # Custom actions
    custom_actions: list[str] = field(default_factory=list)

    # Other configs
    funding: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)

    # Release automation
    release_drafter: bool = False
    auto_release: bool = False


@dataclass(slots=True)
class RepositoryProfile:
    root: Path
    name: str
    total_files: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    categories: dict[str, int] = field(default_factory=dict)
    doc_needs: list[str] = field(default_factory=list)
    file_insights: list[FileInsight] = field(default_factory=list)
    existing_docs: list[Path] = field(default_factory=list)
    detected_tools: list[str] = field(default_factory=list)
    detected_frameworks: list[str] = field(default_factory=list)

    # Enhanced fields
    dependencies: list[Dependency] = field(default_factory=list)
    env_variables: list[EnvVariable] = field(default_factory=list)
    entry_points: list[EntryPoint] = field(default_factory=list)
    config_files: list[ConfigFile] = field(default_factory=list)
    api_endpoints: list[APIEndpoint] = field(default_factory=list)
    scripts: list[Script] = field(default_factory=list)

    # CI/CD workflows
    ci_workflows: list["CIWorkflow"] = field(default_factory=list)

    # GitHub configuration
    github_config: "GitHubConfig | None" = None

    # Semantic understanding (populated by LLM)
    purpose_summary: str = ""
    architecture_summary: str = ""
    key_concepts: list[str] = field(default_factory=list)

    # Directory summaries for complete codebase understanding
    directory_summaries: list["DirectorySummary"] = field(default_factory=list)

    # Raw content cache for important files
    important_file_contents: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentationArtifact:
    filename: str
    title: str
    body: str
    generated_with_ai: bool = False


@dataclass(slots=True)
class GenerationResult:
    profile: RepositoryProfile
    artifacts: list[DocumentationArtifact]
    warnings: list[str] = field(default_factory=list)


# Compliance and Security Models

@dataclass(slots=True)
class ComplianceFinding:
    """A single compliance violation or security finding."""
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "phi", "pii", "credential", "secret"
    file_path: Path
    line_number: int | None = None
    pattern_matched: str = ""
    description: str = ""
    recommendation: str = ""
    data_sample: str = ""  # Redacted sample for context


@dataclass(slots=True)
class ComplianceReport:
    """Compliance scan results for a repository."""
    scan_timestamp: str = ""
    repo_name: str = ""
    repo_path: str = ""

    # Findings by severity
    critical_findings: list[ComplianceFinding] = field(default_factory=list)
    high_findings: list[ComplianceFinding] = field(default_factory=list)
    medium_findings: list[ComplianceFinding] = field(default_factory=list)
    low_findings: list[ComplianceFinding] = field(default_factory=list)

    # Summary counts
    total_files_scanned: int = 0
    files_with_findings: int = 0

    # Compliance status
    hipaa_compliant: bool = True
    pci_compliant: bool = True
    ai_safe: bool = True  # Safe to send to external AI

    # Blocked operations
    ai_blocked_reason: str = ""

    @property
    def total_findings(self) -> int:
        return (len(self.critical_findings) + len(self.high_findings) +
                len(self.medium_findings) + len(self.low_findings))

    @property
    def has_blockers(self) -> bool:
        return len(self.critical_findings) > 0 or len(self.high_findings) > 0
