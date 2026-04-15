from __future__ import annotations

from pathlib import Path

from .models import DocumentationArtifact, RepositoryProfile


class AdaptiveDocGenerator:
    """Generate repository-specific docs from a generic intelligence profile."""

    def __init__(self, template_dir: Path | None = None) -> None:
        self.template_dir = template_dir or Path(__file__).resolve().parents[2] / "templates"

    def generate(self, profile: RepositoryProfile) -> list[DocumentationArtifact]:
        artifacts: list[DocumentationArtifact] = []

        for need in profile.doc_needs:
            artifacts.append(self._build_artifact(need, profile))

        return artifacts

    def _build_artifact(self, need: str, profile: RepositoryProfile) -> DocumentationArtifact:
        builders = {
            "repository-overview": self._repository_overview,
            "architecture-guide": self._architecture_guide,
            "developer-workflows": self._developer_workflows,
            "quality-and-validation": self._quality_and_validation,
            "getting-started": self._getting_started,
            "usage-patterns": self._usage_patterns,
            "configuration-guide": self._configuration_guide,
            "deployment-runbook": self._deployment_runbook,
            "api-reference": self._api_reference,
            "operations-runbook": self._operations_runbook,
        }

        builder = builders.get(need)
        if builder:
            return DocumentationArtifact(
                filename=f"{need.upper().replace('-', '_')}.md",
                title=f"{profile.name} {need.replace('-', ' ').title()}",
                body=builder(profile),
            )

        return DocumentationArtifact(
            filename=f"{need.upper().replace('-', '_')}.md",
            title=need.replace("-", " ").title(),
            body="Documentation template not yet specialized.",
        )

    def _repository_overview(self, profile: RepositoryProfile) -> str:
        top_languages = self._format_counter(profile.languages)
        top_categories = self._format_counter(profile.categories)
        tools = ", ".join(profile.detected_tools) if profile.detected_tools else "None detected"
        frameworks = ", ".join(profile.detected_frameworks) if profile.detected_frameworks else "None detected"

        lines = [
            f"# {profile.name} Repository Overview",
            "",
        ]

        if profile.purpose_summary:
            lines.extend([
                "## What This Repository Does",
                "",
                profile.purpose_summary,
                "",
            ])

        lines.extend([
            "## At a Glance",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Files | {profile.total_files} |",
            f"| Primary Language | {list(profile.languages.keys())[0] if profile.languages else 'Unknown'} |",
            f"| Build Tools | {tools} |",
            f"| Frameworks | {frameworks} |",
            "",
            "## Language Distribution",
            "",
            top_languages,
            "",
            "## Content Categories",
            "",
            top_categories,
            "",
        ])

        if profile.dependencies:
            prod_deps = [d for d in profile.dependencies if not d.dev_only][:15]
            dev_deps = [d for d in profile.dependencies if d.dev_only][:10]
            lines.extend(["## Dependencies", ""])
            if prod_deps:
                lines.append("**Runtime**: " + ", ".join(f"`{d.name}`" for d in prod_deps))
            if dev_deps:
                lines.append("\n**Development**: " + ", ".join(f"`{d.name}`" for d in dev_deps))
            lines.append("")

        if profile.entry_points:
            lines.extend([
                "## Entry Points",
                "",
                "| Name | Type | Command |",
                "|------|------|---------|",
            ])
            for entry in profile.entry_points:
                cmd = f"`{entry.command}`" if entry.command else "-"
                lines.append(f"| {entry.name} | {entry.entry_type} | {cmd} |")
            lines.append("")

        if profile.key_concepts:
            lines.extend([
                "## Key Concepts",
                "",
                *[f"- **{concept}**" for concept in profile.key_concepts],
                "",
            ])

        if profile.architecture_summary:
            lines.extend([
                "## Architecture Overview",
                "",
                profile.architecture_summary,
                "",
            ])

        lines.extend([
            "## Documentation Set",
            "",
            *[f"- {need.replace('-', ' ').title()}" for need in profile.doc_needs],
        ])

        return "\n".join(lines)

    def _architecture_guide(self, profile: RepositoryProfile) -> str:
        app_files = [f for f in profile.file_insights if f.doc_signal == "architecture"][:15]
        entry_files = [f for f in profile.file_insights if f.is_entry_point]

        # Group files by directory
        dirs: dict[str, list[str]] = {}
        for f in app_files:
            parent = str(f.path.parent) if f.path.parent != f.path else "root"
            dirs.setdefault(parent, []).append(f.path.name)

        lines = [
            f"# {profile.name} Architecture Guide",
            "",
        ]

        if profile.architecture_summary:
            lines.extend([
                "## Overview",
                "",
                profile.architecture_summary,
                "",
            ])

        lines.extend([
            "## Directory Structure",
            "",
            "```",
            f"{profile.name}/",
        ])
        for dir_path, files in sorted(dirs.items())[:10]:
            lines.append(f"├── {dir_path}/")
            for f in files[:5]:
                lines.append(f"│   ├── {f}")
        lines.extend(["```", ""])

        if entry_files:
            lines.extend([
                "## Entry Points",
                "",
            ])
            for f in entry_files:
                lines.append(f"- `{f.path}` - {f.language} entry point")
            lines.append("")

        # Key classes and functions WITH descriptions
        if profile.directory_summaries:
            lines.extend([
                "## Key Classes and Functions",
                "",
            ])
            for dir_sum in profile.directory_summaries[:10]:
                if dir_sum.symbols:
                    lines.append(f"### {dir_sum.path}/")
                    lines.append("")
                    classes = [s for s in dir_sum.symbols if s.symbol_type == "class"][:8]
                    functions = [s for s in dir_sum.symbols if s.symbol_type == "function"][:8]

                    if classes:
                        lines.append("**Classes:**")
                        for cls in classes:
                            desc = f" - {cls.docstring}" if cls.docstring else ""
                            lines.append(f"- `{cls.name}`{desc}")
                        lines.append("")

                    if functions:
                        lines.append("**Functions:**")
                        for func in functions:
                            desc = f" - {func.docstring}" if func.docstring else ""
                            lines.append(f"- `{func.name}{func.signature}`{desc}")
                        lines.append("")

        lines.extend([
            "## Extension Points",
            "",
            "Where to add new functionality:",
            "- **New features**: Look at existing patterns in the application directories",
            "- **New integrations**: Check connections/providers patterns",
            "- **New tests**: Mirror the structure in tests/ directory",
        ])

        return "\n".join(lines)

    def _developer_workflows(self, profile: RepositoryProfile) -> str:
        automation_files = [
            insight for insight in profile.file_insights if insight.doc_signal in {"workflow", "operational"}
        ][:12]

        lines = [
            f"# {profile.name} Developer Workflows",
            "",
            "## Purpose",
            "This guide captures the workflows contributors need to build, test, run, and maintain the repository without tying the guidance to a single platform.",
            "",
            "## Workflow-Relevant Files",
            *(
                [f"- `{item.path}` ({item.category})" for item in automation_files]
                if automation_files
                else ["- No workflow-specific files were detected during the scan."]
            ),
            "",
        ]

        # Add scripts/commands section
        if profile.scripts:
            lines.extend([
                "## Available Development Commands",
                "",
                "| Command | Description |",
                "|---------|-------------|",
            ])
            for script in profile.scripts[:15]:
                desc = script.description or script.name.replace("-", " ").replace("_", " ").title()
                lines.append(f"| `{script.command}` | {desc} |")
            lines.append("")

        # Add GitHub config if present (this is the RIGHT place for it)
        if profile.github_config:
            gh = profile.github_config
            lines.extend([
                "## GitHub Repository Configuration",
                "",
            ])
            if gh.codeowners:
                lines.extend([
                    "### Code Ownership",
                    "",
                    "| Path Pattern | Owner |",
                    "|--------------|-------|",
                ])
                for rule in gh.codeowners[:10]:
                    parts = rule.split()
                    if len(parts) >= 2:
                        lines.append(f"| `{parts[0]}` | {' '.join(parts[1:])} |")
                lines.append("")

            if gh.dependabot_enabled:
                lines.extend([
                    "### Dependabot",
                    "",
                    f"Automated dependency updates enabled for: {', '.join(gh.dependabot_ecosystems)}",
                    "",
                ])

            if gh.issue_templates:
                lines.extend([
                    "### Issue Templates",
                    "",
                    *[f"- {t}" for t in gh.issue_templates],
                    "",
                ])

            if gh.pr_template:
                lines.append("### Pull Request Template\n\nPR template is configured.\n")

            if gh.custom_actions:
                lines.extend([
                    "### Custom Actions",
                    "",
                    *[f"- `{a}`" for a in gh.custom_actions],
                    "",
                ])

        return "\n".join(lines)

    def _quality_and_validation(self, profile: RepositoryProfile) -> str:
        test_files = [insight for insight in profile.file_insights if insight.category == "tests"][:12]

        lines = [
            f"# {profile.name} Quality and Validation",
            "",
            "## Purpose",
            "The purpose of this document is to explain how the correctness of the repository is validated and which confidence-building checks should run before a change is merged or released.",
            "",
            "## Observed Test Surface",
            "The following files contain the tests for this repository:",
            "",
            *(
                [f"- `{item.path}` ({item.language})" for item in test_files]
                if test_files
                else ["- No dedicated test files were detected during the scan."]
            ),
            "",
        ]

        # CI/CD Workflows - THIS IS THE PRIMARY LOCATION
        if profile.ci_workflows:
            lines.extend([
                "## CI/CD Pipeline",
                "",
            ])
            for wf in profile.ci_workflows:
                lines.extend([
                    f"### {wf.name}",
                    "",
                    f"- **Platform**: {wf.platform}",
                    f"- **File**: `{wf.file_path}`",
                ])
                if wf.triggers:
                    lines.append(f"- **Triggers**: {', '.join(wf.triggers)}")
                if wf.jobs:
                    lines.append(f"- **Jobs**: {', '.join(wf.jobs)}")
                if wf.environments:
                    lines.append(f"- **Environments**: {', '.join(wf.environments)}")
                if wf.secrets_used:
                    lines.append(f"- **Required Secrets**: {', '.join(wf.secrets_used)}")
                lines.append("")

        # Test commands
        test_commands = [s for s in profile.scripts if any(t in s.name.lower() for t in ["test", "lint", "check", "validate"])]
        if test_commands:
            lines.extend([
                "## Quality Commands",
                "",
                "| Command | Purpose |",
                "|---------|---------|",
            ])
            for cmd in test_commands[:10]:
                purpose = cmd.description or cmd.name.replace("-", " ").replace("_", " ").title()
                lines.append(f"| `{cmd.command}` | {purpose} |")
            lines.append("")

        return "\n".join(lines)

    def _getting_started(self, profile: RepositoryProfile) -> str:
        lines = [
            f"# {profile.name} Getting Started",
            "",
            "## Goal",
            "Give a new contributor enough context to understand what the repository is, how it is organized, and how to begin contributing safely.",
            "",
        ]

        # Prerequisites
        lines.extend([
            "## Prerequisites",
            "",
        ])
        primary_lang = list(profile.languages.keys())[0] if profile.languages else "Unknown"
        if primary_lang == "Python":
            lines.append("- Python 3.10 or higher")
        elif primary_lang == "JavaScript":
            lines.append("- Node.js 18 or higher")
        elif primary_lang == "TypeScript":
            lines.append("- Node.js 18 or higher")
            lines.append("- TypeScript")

        if "docker" in profile.detected_tools:
            lines.append("- Docker (optional, for containerized deployment)")
        if "make" in profile.detected_tools:
            lines.append("- Make (for running build commands)")
        lines.append("")

        # Installation
        lines.extend([
            "## Installation",
            "",
        ])
        install_cmds = [s for s in profile.scripts if any(i in s.name.lower() for i in ["install", "setup", "prepare"])]
        if install_cmds:
            lines.append("```bash")
            for cmd in install_cmds[:3]:
                lines.append(cmd.command)
            lines.append("```")
        else:
            if primary_lang == "Python":
                lines.extend([
                    "```bash",
                    "pip install -e .",
                    "```",
                ])
            elif primary_lang in ("JavaScript", "TypeScript"):
                lines.extend([
                    "```bash",
                    "npm install",
                    "```",
                ])
        lines.append("")

        # Quick start
        lines.extend([
            "## Quick Start",
            "",
        ])
        if profile.entry_points:
            entry = profile.entry_points[0]
            if entry.command:
                lines.extend([
                    "```bash",
                    entry.command,
                    "```",
                ])
        lines.append("")

        lines.extend([
            "## Next Steps",
            "",
            "1. Review the [Repository Overview](REPOSITORY_OVERVIEW.md) for a high-level understanding",
            "2. Check the [Configuration Guide](CONFIGURATION_GUIDE.md) for environment setup",
            "3. Read the [Developer Workflows](DEVELOPER_WORKFLOWS.md) for contribution guidelines",
        ])

        return "\n".join(lines)

    def _usage_patterns(self, profile: RepositoryProfile) -> str:
        example_files = [insight for insight in profile.file_insights if insight.category == "examples"][:12]

        lines = [
            f"# {profile.name} Usage Patterns",
            "",
            "## Goal",
            "This guide documents the most important usage flows, integration examples, and copyable patterns to help consumers succeed quickly with this service.",
            "",
        ]

        if example_files:
            lines.extend([
                "## Example Files",
                "",
                "The following example files demonstrate usage patterns:",
                "",
            ])
            for item in example_files:
                lines.append(f"- `{item.path}` - {item.language}")
            lines.append("")

        # API endpoints as usage examples
        if profile.api_endpoints:
            lines.extend([
                "## API Usage Examples",
                "",
                "The following endpoints are available:",
                "",
                "| Method | Path | Description |",
                "|--------|------|-------------|",
            ])
            for ep in profile.api_endpoints[:10]:
                desc = ep.description or f"Endpoint at {ep.path}"
                lines.append(f"| `{ep.method}` | `{ep.path}` | {desc} |")
            lines.append("")

        # Entry points as usage
        if profile.entry_points:
            lines.extend([
                "## Command Line Usage",
                "",
            ])
            for entry in profile.entry_points[:5]:
                lines.append(f"### {entry.name}")
                lines.append("")
                if entry.command:
                    lines.append(f"```bash\n{entry.command}\n```")
                lines.append("")

        return "\n".join(lines)

    def _format_counter(self, values: dict[str, int]) -> str:
        if not values:
            return "None detected"
        return ", ".join(f"{name} ({count})" for name, count in list(values.items())[:5])

    def _configuration_guide(self, profile: RepositoryProfile) -> str:
        lines = [
            f"# {profile.name} Configuration Guide",
            "",
            "## Environment Variables",
            "",
        ]

        if profile.env_variables:
            lines.append("| Variable | Required | Default | Source |")
            lines.append("|----------|----------|---------|--------|")
            for env in profile.env_variables:
                required = "Yes" if env.required else "No"
                default = env.default_value or "-"
                source = str(env.source_file.name) if env.source_file else "-"
                lines.append(f"| `{env.name}` | {required} | {default} | {source} |")
        else:
            lines.append("No environment variables detected.")

        lines.extend([
            "",
            "## Configuration Files",
            "",
        ])

        if profile.config_files:
            for cfg in profile.config_files:
                lines.append(f"### `{cfg.path}`")
                lines.append(f"- **Type**: {cfg.config_type}")
                lines.append(f"- **Purpose**: {cfg.purpose}")
                lines.append("")
        else:
            lines.append("No configuration files detected.")

        return "\n".join(lines)

    def _deployment_runbook(self, profile: RepositoryProfile) -> str:
        lines = [
            f"# {profile.name} Deployment Runbook",
            "",
            "## Prerequisites",
            "",
        ]

        # List dependencies
        prod_deps = [d for d in profile.dependencies if not d.dev_only]
        if prod_deps:
            lines.append("### Runtime Dependencies")
            lines.append("")
            for dep in prod_deps[:20]:
                ver = f" ({dep.version})" if dep.version else ""
                lines.append(f"- `{dep.name}`{ver}")
            lines.append("")

        # Environment setup
        if profile.env_variables:
            lines.extend([
                "### Required Environment Variables",
                "",
            ])
            required_env = [e for e in profile.env_variables if e.required]
            for env in required_env[:15]:
                lines.append(f"- `{env.name}`")
            lines.append("")

        # Entry points
        lines.extend([
            "## Deployment Steps",
            "",
        ])

        if profile.entry_points:
            lines.append("### Available Entry Points")
            lines.append("")
            for entry in profile.entry_points:
                cmd = f" - `{entry.command}`" if entry.command else ""
                lines.append(f"- **{entry.name}** ({entry.entry_type}){cmd}")
            lines.append("")

        # Docker if detected
        if "docker" in profile.detected_tools:
            lines.extend([
                "### Docker Deployment",
                "",
                "```bash",
                "docker build -t " + profile.name.lower() + " .",
                "docker run -d " + profile.name.lower(),
                "```",
                "",
            ])

        lines.extend([
            "## Rollback Procedure",
            "",
            "1. Identify the last known good version",
            "2. Revert deployment to previous version",
            "3. Verify service health",
            "4. Investigate root cause",
            "",
            "## Health Checks",
            "",
            "- [ ] Service responds to health endpoint",
            "- [ ] Logs show no errors",
            "- [ ] Metrics are within normal range",
        ])

        return "\n".join(lines)

    def _api_reference(self, profile: RepositoryProfile) -> str:
        lines = [
            f"# {profile.name} API Reference",
            "",
        ]

        if profile.api_endpoints:
            # Group by path prefix
            lines.extend([
                "## Endpoints",
                "",
                "| Method | Path | Source |",
                "|--------|------|--------|",
            ])
            for endpoint in profile.api_endpoints:
                source = str(endpoint.source_file) if endpoint.source_file else "-"
                lines.append(f"| `{endpoint.method}` | `{endpoint.path}` | {source} |")
        else:
            lines.extend([
                "No API endpoints were automatically detected.",
                "",
                "If this repository exposes an API, document endpoints here.",
            ])

        return "\n".join(lines)

    def _operations_runbook(self, profile: RepositoryProfile) -> str:
        lines = [
            f"# {profile.name} Operations Runbook",
            "",
            "## Available Commands",
            "",
        ]

        if profile.scripts:
            lines.append("| Command | Description | Source |")
            lines.append("|---------|-------------|--------|")
            for script in profile.scripts:
                desc = script.description or "-"
                lines.append(f"| `{script.command}` | {desc} | {script.source} |")
            lines.append("")
        else:
            lines.append("No scripts detected.")
            lines.append("")

        lines.extend([
            "## Common Operations",
            "",
            "### Starting the Service",
            "",
        ])

        # Infer start command
        if any(s.name in {"start", "serve", "run", "dev"} for s in profile.scripts):
            start_script = next(s for s in profile.scripts if s.name in {"start", "serve", "run", "dev"})
            lines.append(f"```bash\n{start_script.command}\n```")
        elif profile.entry_points:
            entry = profile.entry_points[0]
            if entry.command:
                lines.append(f"```bash\n{entry.command}\n```")
        else:
            lines.append("Refer to project documentation for start command.")

        lines.extend([
            "",
            "### Stopping the Service",
            "",
            "- Graceful shutdown: Send SIGTERM",
            "- Force stop: Send SIGKILL",
            "",
            "## Troubleshooting",
            "",
            "### Common Issues",
            "",
            "| Symptom | Possible Cause | Resolution |",
            "|---------|----------------|------------|",
            "| Service won't start | Missing env vars | Check configuration guide |",
            "| Connection refused | Service not running | Check process status |",
            "| High latency | Resource exhaustion | Check system resources |",
            "",
            "### Log Locations",
            "",
            "- Application logs: Check stdout/stderr or logging configuration",
            "- Error logs: Review application error handlers",
        ])

        return "\n".join(lines)
