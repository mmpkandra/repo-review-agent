from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .models import (
    APIEndpoint,
    CIWorkflow,
    ComplianceReport,
    ConfigFile,
    Dependency,
    DirectorySummary,
    EntryPoint,
    EnvVariable,
    FileInsight,
    GitHubConfig,
    RepositoryProfile,
    Script,
)
from .compliance_scanner import ComplianceScanner

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".jsx": "JavaScript React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
}

DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc"}
IGNORE_DIRS = {
    ".git",
    ".next",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".pytest_cache",
    "__pycache__",
}

# Files that are important for understanding a repo
IMPORTANT_FILES = {
    "readme.md", "readme.rst", "readme.txt", "readme",
    "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "cargo.toml", "go.mod",
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "makefile", ".env.example", ".env.sample",
    "requirements.txt", "requirements-dev.txt",
    "main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs",
}


class RepositoryAnalyzer:
    """Build a generic intelligence profile for an arbitrary repository."""

    def __init__(
        self,
        max_file_content_size: int = 100000,  # 100KB per file
        max_total_context_size: int = 500000,  # 500KB total context
        max_important_files: int = 30,  # Cache more files
        compliance_scan: bool = False,  # Enable compliance scanning
        compliance_level: str = "standard",  # quick, standard, thorough
        generate_all_docs: bool = False,  # Generate all doc types
        verbose: bool = True,  # Show progress
    ) -> None:
        self.max_file_content_size = max_file_content_size
        self.max_total_context_size = max_total_context_size
        self.max_important_files = max_important_files
        self.compliance_scan = compliance_scan
        self.compliance_level = compliance_level
        self.generate_all_docs = generate_all_docs
        self.verbose = verbose
        self.compliance_scanner = ComplianceScanner(scan_level=compliance_level) if compliance_scan else None
        self.compliance_report: ComplianceReport | None = None

    def _log(self, message: str, end: str = "\n") -> None:
        """Print progress message if verbose mode is enabled."""
        if self.verbose:
            print(message, end=end, flush=True)

    def analyze(self, root: Path) -> RepositoryProfile:
        root = root.resolve()
        profile = RepositoryProfile(root=root, name=root.name)
        languages: Counter[str] = Counter()
        categories: Counter[str] = Counter()

        self._log(f"Analyzing repository: {root.name}")
        self._log("  [1/6] Scanning files...", end=" ")

        # First pass: collect all files and basic info
        for file_path in self._iter_files(root):
            relative_path = file_path.relative_to(root)
            language = self._detect_language(file_path)
            category = self._categorize(relative_path)
            doc_signal = self._doc_signal(relative_path, category)
            is_entry = self._is_entry_point(relative_path)
            importance = self._calculate_importance(relative_path, category, is_entry)

            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                size_bytes = 0

            profile.total_files += 1
            languages[language] += 1
            categories[category] += 1
            profile.file_insights.append(
                FileInsight(
                    path=relative_path,
                    category=category,
                    language=language,
                    doc_signal=doc_signal,
                    size_bytes=size_bytes,
                    is_entry_point=is_entry,
                    importance_score=importance,
                )
            )

            if file_path.suffix.lower() in DOC_EXTENSIONS:
                profile.existing_docs.append(relative_path)

            self._detect_repo_markers(relative_path, profile)

        profile.languages = dict(languages.most_common())
        profile.categories = dict(categories.most_common())
        self._log(f"{profile.total_files} files found")

        # Second pass: deep extraction
        self._log("  [2/6] Extracting dependencies & configs...", end=" ")
        self._extract_dependencies(root, profile)
        self._extract_env_variables(root, profile)
        self._extract_entry_points(root, profile)
        self._extract_config_files(root, profile)
        self._extract_scripts(root, profile)
        self._extract_api_endpoints(root, profile)
        self._extract_ci_workflows(root, profile)
        self._log("DONE")

        # Third pass: extract code structure from ALL files
        self._log("  [3/6] Extracting code structure...", end=" ")
        self._extract_code_structure(root, profile)
        classes = sum(len(f.classes) for f in profile.file_insights)
        functions = sum(len(f.functions) for f in profile.file_insights)
        self._log(f"{classes} classes, {functions} functions")

        # Fourth pass: build directory summaries
        self._log("  [4/6] Building directory summaries...", end=" ")
        self._build_directory_summaries(profile)
        self._log(f"{len(profile.directory_summaries)} directories")

        # Cache important files
        self._log("  [5/6] Caching important files...", end=" ")
        self._cache_important_files(root, profile)
        self._log(f"{len(profile.important_file_contents)} files cached")

        profile.doc_needs = self._infer_doc_needs(profile, generate_all=self.generate_all_docs)
        profile.detected_tools = sorted(set(profile.detected_tools))
        profile.detected_frameworks = sorted(set(profile.detected_frameworks))

        # Run compliance scan if enabled
        if self.compliance_scan and self.compliance_scanner:
            self._log("  [6/6] Running compliance scan...", end=" ")
            self.compliance_report = self.compliance_scanner.scan_repository(root)
            self._log(f"{self.compliance_report.total_findings} findings")
        else:
            self._log("  [6/6] Compliance scan... SKIPPED")

        self._log(f"Analysis complete. Documents to generate: {len(profile.doc_needs)}")
        return profile

    def _is_entry_point(self, relative_path: Path) -> bool:
        name = relative_path.name.lower()
        return name in {
            "main.py", "app.py", "__main__.py", "cli.py", "server.py",
            "index.js", "index.ts", "main.js", "main.ts", "app.js", "app.ts",
            "main.go", "main.rs", "main.java",
        }

    def _calculate_importance(self, relative_path: Path, category: str, is_entry: bool) -> float:
        score = 0.0
        name = relative_path.name.lower()

        if is_entry:
            score += 0.4
        if name in IMPORTANT_FILES:
            score += 0.3
        if category == "application":
            score += 0.2
        if category in {"infrastructure", "automation"}:
            score += 0.1
        if len(relative_path.parts) <= 2:  # Closer to root = more important
            score += 0.1

        return min(score, 1.0)

    def _iter_files(self, root: Path):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            yield path

    def _detect_language(self, path: Path) -> str:
        return LANGUAGE_MAP.get(path.suffix.lower(), "Other")

    def _categorize(self, relative_path: Path) -> str:
        parts = {part.lower() for part in relative_path.parts}
        name = relative_path.name.lower()

        if relative_path.suffix.lower() in DOC_EXTENSIONS or "docs" in parts:
            return "documentation"
        if "test" in parts or "tests" in parts or name.startswith("test_"):
            return "tests"
        if "scripts" in parts or name.endswith(".sh"):
            return "automation"
        if "infra" in parts or ".github" in parts or "docker" in name:
            return "infrastructure"
        if {
            "src",
            "app",
            "lib",
            "pages",
            "components",
            "hooks",
            "utils",
            "services",
            "server",
            "client",
        } & parts:
            return "application"
        if "examples" in parts:
            return "examples"
        return "misc"

    def _doc_signal(self, relative_path: Path, category: str) -> str:
        name = relative_path.name.lower()
        if category == "infrastructure":
            return "operational"
        if category == "application":
            return "architecture"
        if category == "tests":
            return "quality"
        if "api" in name or "schema" in name:
            return "interface"
        if category == "automation":
            return "workflow"
        return "overview"

    def _detect_repo_markers(self, relative_path: Path, profile: RepositoryProfile) -> None:
        marker = relative_path.name.lower()
        marker_path = str(relative_path).lower()

        if marker == "pyproject.toml":
            profile.detected_tools.append("setuptools/pyproject")
        if marker == "package.json":
            profile.detected_tools.append("npm")
        if marker == "cargo.toml":
            profile.detected_tools.append("cargo")
        if marker == "dockerfile":
            profile.detected_tools.append("docker")
        if marker == "makefile":
            profile.detected_tools.append("make")

        # Infrastructure as Code (IaC) tools
        if relative_path.suffix.lower() == ".tf" or marker in {"main.tf", "variables.tf", "outputs.tf"}:
            profile.detected_tools.append("terraform")
        if marker in {"playbook.yml", "playbook.yaml", "site.yml", "ansible.cfg"}:
            profile.detected_tools.append("ansible")
        if marker in {"chart.yaml", "chart.yml"}:
            profile.detected_tools.append("helm")
        if marker in {"kustomization.yaml", "kustomization.yml"}:
            profile.detected_tools.append("kustomize")
        if marker == "pulumi.yaml" or marker == "pulumi.yml":
            profile.detected_tools.append("pulumi")
        if "cloudformation" in marker_path or marker.endswith(".template"):
            profile.detected_tools.append("cloudformation")

        # Frameworks
        if "fastapi" in marker_path:
            profile.detected_frameworks.append("FastAPI")
        if "django" in marker_path:
            profile.detected_frameworks.append("Django")
        if "react" in marker_path or relative_path.suffix.lower() in {".tsx", ".jsx"}:
            profile.detected_frameworks.append("React")

    def _infer_doc_needs(self, profile: RepositoryProfile, generate_all: bool = False) -> list[str]:
        """Determine which documents to generate.

        Args:
            profile: Repository profile with extracted data
            generate_all: If True, generate all document types regardless of detection
        """
        # All possible document types
        all_docs = [
            "repository-overview",
            "architecture-guide",
            "configuration-guide",
            "deployment-runbook",
            "operations-runbook",
            "api-reference",
            "quality-and-validation",
            "usage-patterns",
            "developer-workflows",
        ]

        if generate_all:
            return all_docs

        needs: list[str] = ["repository-overview"]
        categories = profile.categories

        # Detect repo type
        is_infra_repo = self._is_infrastructure_repo(profile)
        is_app_repo = categories.get("application", 0) > 0 or profile.languages.get("Python", 0) > 5 or profile.languages.get("JavaScript", 0) > 5

        # Architecture guide - for both app and infra repos
        if is_app_repo or is_infra_repo or profile.total_files > 10:
            needs.append("architecture-guide")

        # Developer workflows - almost always useful
        if profile.total_files > 5:
            needs.append("developer-workflows")

        # Quality & validation - if tests exist or code that should be tested
        if categories.get("tests", 0) or is_app_repo or is_infra_repo:
            needs.append("quality-and-validation")

        # Configuration guide - critical for infra repos, useful for apps
        if is_infra_repo or profile.env_variables or profile.config_files or profile.languages.get("YAML", 0) > 0 or profile.languages.get("JSON", 0) > 3:
            needs.append("configuration-guide")

        # Deployment runbook - essential for infra, useful for apps with deploy files
        if is_infra_repo or "docker" in profile.detected_tools or any(
            any(kw in str(f.path).lower() for kw in ["deploy", "dockerfile", "kubernetes", "k8s", "helm"])
            for f in profile.file_insights
        ):
            needs.append("deployment-runbook")

        # Operations runbook - for both infra and apps with scripts
        if is_infra_repo or profile.scripts or "make" in profile.detected_tools or "npm" in profile.detected_tools:
            needs.append("operations-runbook")

        # Usage patterns - examples or substantial content
        if categories.get("examples", 0) or profile.total_files > 20:
            needs.append("usage-patterns")

        # API reference - only for API projects
        if profile.api_endpoints or any(
            f in profile.detected_frameworks for f in ["FastAPI", "Flask", "Django", "Express"]
        ):
            needs.append("api-reference")

        return needs

    def _is_infrastructure_repo(self, profile: RepositoryProfile) -> bool:
        """Detect if this is an infrastructure/IaC repository."""
        infra_indicators = 0

        # Check for IaC tools
        infra_tools = {"terraform", "ansible", "pulumi", "cloudformation", "helm", "kustomize"}
        for tool in profile.detected_tools:
            if tool.lower() in infra_tools:
                infra_indicators += 2

        # Check for infra file extensions
        infra_extensions = {".tf", ".tfvars", ".hcl"}  # Terraform
        infra_extensions.update({".yaml", ".yml"})  # K8s, Ansible, CloudFormation
        infra_extensions.update({".j2", ".jinja2"})  # Ansible templates

        for insight in profile.file_insights:
            ext = insight.path.suffix.lower()
            name = insight.path.name.lower()

            if ext in infra_extensions:
                infra_indicators += 0.5

            # Specific infra file patterns
            if ext == ".tf" or name.endswith(".tf"):
                infra_indicators += 2
            if name in {"main.tf", "variables.tf", "outputs.tf", "providers.tf", "backend.tf"}:
                infra_indicators += 3
            if name in {"playbook.yml", "playbook.yaml", "site.yml", "site.yaml"}:
                infra_indicators += 3  # Ansible
            if name in {"chart.yaml", "values.yaml"}:
                infra_indicators += 3  # Helm
            if name in {"kustomization.yaml", "kustomization.yml"}:
                infra_indicators += 3  # Kustomize
            if "cloudformation" in str(insight.path).lower():
                infra_indicators += 2
            if any(kw in str(insight.path).lower() for kw in ["terraform", "infra", "infrastructure", "iac", "modules"]):
                infra_indicators += 1

        # Check categories
        if profile.categories.get("infrastructure", 0) > profile.categories.get("application", 0):
            infra_indicators += 3

        return infra_indicators >= 5

    def _read_file_safe(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8")
            return content[: self.max_file_content_size]
        except (UnicodeDecodeError, OSError):
            return ""

    def _extract_dependencies(self, root: Path, profile: RepositoryProfile) -> None:
        # Python: pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            self._parse_pyproject_deps(pyproject, profile)

        # Python: requirements.txt
        for req_file in ["requirements.txt", "requirements-dev.txt"]:
            req_path = root / req_file
            if req_path.exists():
                self._parse_requirements_txt(req_path, profile, dev="dev" in req_file)

        # Node: package.json
        pkg_json = root / "package.json"
        if pkg_json.exists():
            self._parse_package_json_deps(pkg_json, profile)

    def _parse_pyproject_deps(self, path: Path, profile: RepositoryProfile) -> None:
        content = self._read_file_safe(path)
        in_deps = False
        in_dev_deps = False

        for line in content.splitlines():
            line_stripped = line.strip()

            # Standard pyproject.toml format
            if line_stripped == "[project.dependencies]" or line_stripped.startswith("dependencies = ["):
                in_deps = True
                in_dev_deps = False
                continue

            # Poetry format: [tool.poetry.dependencies]
            if line_stripped == "[tool.poetry.dependencies]":
                in_deps = True
                in_dev_deps = False
                continue

            # Poetry dev dependencies
            if "[tool.poetry.group.dev" in line_stripped:
                in_deps = True
                in_dev_deps = True
                continue

            # Standard dev dependencies
            if "dev" in line_stripped.lower() and "dependencies" in line_stripped.lower():
                in_deps = True
                in_dev_deps = True
                continue

            # End of section
            if line_stripped.startswith("[") and in_deps:
                in_deps = False
                continue

            if in_deps:
                # Poetry format: package = "version" or package = {version = "..."}
                if "=" in line_stripped and not line_stripped.startswith("#"):
                    parts = line_stripped.split("=", 1)
                    dep_name = parts[0].strip().strip('"\'')
                    # Skip python version constraint and comments
                    if dep_name and dep_name != "python" and not dep_name.startswith("#"):
                        profile.dependencies.append(
                            Dependency(name=dep_name, dev_only=in_dev_deps, source="pyproject.toml")
                        )
                # Standard format: "package>=version"
                elif line_stripped.startswith('"'):
                    dep = line_stripped.strip('",').split(">=")[0].split("==")[0].split("<")[0].strip()
                    if dep:
                        profile.dependencies.append(
                            Dependency(name=dep, dev_only=in_dev_deps, source="pyproject.toml")
                        )

    def _parse_requirements_txt(self, path: Path, profile: RepositoryProfile, dev: bool = False) -> None:
        content = self._read_file_safe(path)
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            dep = re.split(r"[>=<\[!]", line)[0].strip()
            if dep:
                profile.dependencies.append(Dependency(name=dep, dev_only=dev, source=path.name))

    def _parse_package_json_deps(self, path: Path, profile: RepositoryProfile) -> None:
        content = self._read_file_safe(path)
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return
        for dep, ver in data.get("dependencies", {}).items():
            profile.dependencies.append(Dependency(name=dep, version=ver, source="package.json"))
        for dep, ver in data.get("devDependencies", {}).items():
            profile.dependencies.append(Dependency(name=dep, version=ver, dev_only=True, source="package.json"))

    def _extract_env_variables(self, root: Path, profile: RepositoryProfile) -> None:
        # Check .env.example, .env.sample
        for env_file in [".env.example", ".env.sample", ".env.template"]:
            env_path = root / env_file
            if env_path.exists():
                self._parse_env_file(env_path, profile)

        # Scan Python files for os.getenv / os.environ
        for insight in profile.file_insights:
            if insight.language == "Python":
                self._scan_python_for_env(root / insight.path, profile)

    def _parse_env_file(self, path: Path, profile: RepositoryProfile) -> None:
        content = self._read_file_safe(path)
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=")[0].strip()
                default = line.split("=", 1)[1].strip() if "=" in line else None
                profile.env_variables.append(EnvVariable(
                    name=key,
                    source_file=path,
                    default_value=default if default else None,
                ))

    def _scan_python_for_env(self, path: Path, profile: RepositoryProfile) -> None:
        content = self._read_file_safe(path)
        existing = {e.name for e in profile.env_variables}
        # Patterns for environment variable access (must be uppercase, min 3 chars)
        patterns = [
            r'os\.getenv\(["\']([A-Z][A-Z0-9_]{2,})["\']',
            r'os\.environ\[["\']([A-Z][A-Z0-9_]{2,})["\']\]',
            r'os\.environ\.get\(["\']([A-Z][A-Z0-9_]{2,})["\']',
        ]
        for line in content.splitlines():
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in patterns:
                for match in re.finditer(pattern, line):
                    var_name = match.group(1)
                    if var_name not in existing:
                        existing.add(var_name)
                        profile.env_variables.append(EnvVariable(name=var_name, source_file=path))

    def _extract_entry_points(self, root: Path, profile: RepositoryProfile) -> None:
        # From pyproject.toml scripts (standard and Poetry format)
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            content = self._read_file_safe(pyproject)
            in_scripts = False
            for line in content.splitlines():
                # Both standard and Poetry formats
                if "[project.scripts]" in line or "[tool.poetry.scripts]" in line:
                    in_scripts = True
                    continue
                if line.strip().startswith("[") and in_scripts:
                    break
                if in_scripts and "=" in line and not line.strip().startswith("#"):
                    name, target = line.split("=", 1)
                    name = name.strip().strip('"\'')
                    target = target.strip().strip('"\'')
                    if name:
                        profile.entry_points.append(EntryPoint(
                            name=name,
                            path=pyproject,
                            entry_type="cli",
                            command=name,
                            description=f"CLI entry: {target}",
                        ))

        # From package.json bin/main
        pkg_json = root / "package.json"
        if pkg_json.exists():
            content = self._read_file_safe(pkg_json)
            try:
                data = json.loads(content)
                if "main" in data:
                    profile.entry_points.append(EntryPoint(
                        name="main",
                        path=root / data["main"],
                        entry_type="module",
                        description=f"Main entry: {data['main']}",
                    ))
                for name, cmd in data.get("bin", {}).items():
                    profile.entry_points.append(EntryPoint(
                        name=name, path=root / cmd, entry_type="cli", command=name
                    ))
            except json.JSONDecodeError:
                pass

        # Detect __main__.py
        for insight in profile.file_insights:
            if insight.path.name == "__main__.py":
                module = insight.path.parent.name
                profile.entry_points.append(EntryPoint(
                    name=module,
                    path=insight.path,
                    entry_type="module",
                    command=f"python -m {module}",
                ))

    def _extract_config_files(self, root: Path, profile: RepositoryProfile) -> None:
        config_patterns = {
            ".env.example": "env",
            ".env.sample": "env",
            "config.yaml": "yaml",
            "config.yml": "yaml",
            "config.json": "json",
            "settings.json": "json",
            "tsconfig.json": "json",
            ".eslintrc.json": "json",
            "pyproject.toml": "toml",
            "setup.cfg": "ini",
        }
        for insight in profile.file_insights:
            name = insight.path.name.lower()
            if name in config_patterns:
                profile.config_files.append(ConfigFile(
                    path=insight.path,
                    config_type=config_patterns[name],
                    purpose=self._infer_config_purpose(name),
                ))

    def _infer_config_purpose(self, name: str) -> str:
        purposes = {
            ".env": "Environment variables",
            "config": "Application configuration",
            "tsconfig": "TypeScript compiler options",
            ".eslintrc": "ESLint rules",
            "pyproject": "Python project metadata and dependencies",
            "setup.cfg": "Python package configuration",
        }
        for key, purpose in purposes.items():
            if key in name:
                return purpose
        return "Configuration"

    def _extract_scripts(self, root: Path, profile: RepositoryProfile) -> None:
        # package.json scripts
        pkg_json = root / "package.json"
        if pkg_json.exists():
            content = self._read_file_safe(pkg_json)
            try:
                data = json.loads(content)
                for name, cmd in data.get("scripts", {}).items():
                    profile.scripts.append(Script(
                        name=name, command=cmd, source="package.json"
                    ))
            except json.JSONDecodeError:
                pass

        # Makefile targets
        makefile = root / "Makefile"
        if makefile.exists():
            content = self._read_file_safe(makefile)
            for match in re.finditer(r"^([a-zA-Z_][a-zA-Z0-9_-]*):", content, re.MULTILINE):
                target = match.group(1)
                if not target.startswith("."):
                    profile.scripts.append(Script(
                        name=target, command=f"make {target}", source="Makefile"
                    ))

    def _extract_api_endpoints(self, root: Path, profile: RepositoryProfile) -> None:
        # Scan for FastAPI/Flask route decorators
        route_patterns = [
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@app\.route\(["\']([^"\']+)["\'].*methods=\[([^\]]+)\]',
        ]
        for insight in profile.file_insights:
            if insight.language == "Python":
                content = self._read_file_safe(root / insight.path)
                for pattern in route_patterns[:2]:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        method, path = match.group(1).upper(), match.group(2)
                        profile.api_endpoints.append(APIEndpoint(
                            path=path, method=method, source_file=insight.path
                        ))
                # Flask style
                for match in re.finditer(route_patterns[2], content):
                    path, methods = match.group(1), match.group(2)
                    for m in re.findall(r'["\'](\w+)["\']', methods):
                        profile.api_endpoints.append(APIEndpoint(
                            path=path, method=m.upper(), source_file=insight.path
                        ))

    def _extract_ci_workflows(self, root: Path, profile: RepositoryProfile) -> None:
        """Extract CI/CD workflow definitions."""
        # GitHub folder - comprehensive extraction
        gh_folder = root / ".github"
        if gh_folder.exists():
            self._parse_github_folder(gh_folder, root, profile)

        # GitHub Actions workflows
        gh_workflows = root / ".github" / "workflows"
        if gh_workflows.exists():
            for wf_file in gh_workflows.glob("*.yml"):
                self._parse_github_workflow(wf_file, profile)
            for wf_file in gh_workflows.glob("*.yaml"):
                self._parse_github_workflow(wf_file, profile)

        # GitLab CI
        gitlab_ci = root / ".gitlab-ci.yml"
        if gitlab_ci.exists():
            self._parse_gitlab_ci(gitlab_ci, profile)

        # Jenkins
        jenkinsfile = root / "Jenkinsfile"
        if jenkinsfile.exists():
            self._parse_jenkinsfile(jenkinsfile, profile)

        # CircleCI
        circleci = root / ".circleci" / "config.yml"
        if circleci.exists():
            self._parse_circleci(circleci, profile)

    def _parse_github_folder(self, gh_folder: Path, root: Path, profile: RepositoryProfile) -> None:
        """Parse all GitHub configuration from .github/ folder."""
        config = GitHubConfig()

        # CODEOWNERS
        codeowners = gh_folder / "CODEOWNERS"
        if codeowners.exists():
            content = self._read_file_safe(codeowners)
            # Extract ownership rules (pattern -> owners)
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    config.codeowners.append(line)

        # Dependabot
        dependabot = gh_folder / "dependabot.yml"
        if not dependabot.exists():
            dependabot = gh_folder / "dependabot.yaml"
        if dependabot.exists():
            config.dependabot_enabled = True
            content = self._read_file_safe(dependabot)
            # Extract ecosystems
            ecosystems = re.findall(r'package-ecosystem:\s*["\']?([a-z-]+)', content)
            config.dependabot_ecosystems = list(set(ecosystems))

        # Issue templates
        issue_template_dir = gh_folder / "ISSUE_TEMPLATE"
        if issue_template_dir.exists():
            for tmpl in issue_template_dir.glob("*.md"):
                config.issue_templates.append(tmpl.stem)
            for tmpl in issue_template_dir.glob("*.yml"):
                config.issue_templates.append(tmpl.stem)
            for tmpl in issue_template_dir.glob("*.yaml"):
                config.issue_templates.append(tmpl.stem)

        # Single issue template
        if (gh_folder / "ISSUE_TEMPLATE.md").exists():
            config.issue_templates.append("default")

        # PR template
        if (gh_folder / "PULL_REQUEST_TEMPLATE.md").exists() or (gh_folder / "pull_request_template.md").exists():
            config.pr_template = True

        # Custom actions (reusable workflows and composite actions)
        actions_dir = gh_folder / "actions"
        if actions_dir.exists():
            for action in actions_dir.iterdir():
                if action.is_dir():
                    action_yml = action / "action.yml"
                    if not action_yml.exists():
                        action_yml = action / "action.yaml"
                    if action_yml.exists():
                        config.custom_actions.append(action.name)

        # Reusable workflows
        workflows_dir = gh_folder / "workflows"
        if workflows_dir.exists():
            for wf in workflows_dir.glob("*.yml"):
                content = self._read_file_safe(wf)
                if "workflow_call:" in content:
                    config.custom_actions.append(f"workflow:{wf.stem}")
            for wf in workflows_dir.glob("*.yaml"):
                content = self._read_file_safe(wf)
                if "workflow_call:" in content:
                    config.custom_actions.append(f"workflow:{wf.stem}")

        # Funding
        funding = gh_folder / "FUNDING.yml"
        if not funding.exists():
            funding = gh_folder / "FUNDING.yaml"
        if funding.exists():
            content = self._read_file_safe(funding)
            # Extract funding platforms
            platforms = re.findall(r'^([a-z_]+):', content, re.MULTILINE)
            config.funding = [p for p in platforms if p not in {'custom'}]

        # Labels
        labels_file = gh_folder / "labels.yml"
        if not labels_file.exists():
            labels_file = gh_folder / "labels.yaml"
        if labels_file.exists():
            content = self._read_file_safe(labels_file)
            labels = re.findall(r'name:\s*["\']?([^"\'\n]+)', content)
            config.labels = labels

        # Release drafter
        if (gh_folder / "release-drafter.yml").exists() or (gh_folder / "release-drafter.yaml").exists():
            config.release_drafter = True

        # Auto-release patterns in workflows
        workflows_dir = gh_folder / "workflows"
        if workflows_dir.exists():
            for wf in list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml")):
                content = self._read_file_safe(wf)
                if "release" in wf.stem.lower() or "semantic-release" in content or "release-please" in content:
                    config.auto_release = True
                    break

        # Infer protected branches from workflow triggers
        if workflows_dir.exists():
            protected = set()
            for wf in list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml")):
                content = self._read_file_safe(wf)
                # Look for branch protection patterns
                branches = re.findall(r'branches:\s*\[([^\]]+)\]', content)
                for branch_list in branches:
                    for b in branch_list.split(','):
                        b = b.strip().strip('"\'')
                        if b in {'main', 'master', 'develop', 'release/*', 'production'}:
                            protected.add(b)
            config.protected_branches = list(protected)

        profile.github_config = config
        profile.detected_tools.append("github")

    def _parse_github_workflow(self, wf_file: Path, profile: RepositoryProfile) -> None:
        """Parse GitHub Actions workflow file."""
        content = self._read_file_safe(wf_file)
        if not content:
            return

        workflow = CIWorkflow(
            name=wf_file.stem,
            file_path=wf_file.relative_to(profile.root) if wf_file.is_relative_to(profile.root) else wf_file,
            platform="github-actions",
        )

        # Try YAML parsing first, fall back to regex
        if YAML_AVAILABLE:
            try:
                data = yaml.safe_load(content)
                if data:
                    workflow.name = data.get("name", wf_file.stem)

                    # Extract triggers
                    if "on" in data:
                        triggers = data["on"]
                        if isinstance(triggers, list):
                            workflow.triggers = triggers
                        elif isinstance(triggers, dict):
                            workflow.triggers = list(triggers.keys())
                        elif isinstance(triggers, str):
                            workflow.triggers = [triggers]

                    # Extract jobs
                    if "jobs" in data and isinstance(data["jobs"], dict):
                        workflow.jobs = list(data["jobs"].keys())

                        # Extract environments and secrets from jobs
                        for job_name, job_def in data["jobs"].items():
                            if isinstance(job_def, dict):
                                if "environment" in job_def:
                                    env = job_def["environment"]
                                    if isinstance(env, str):
                                        workflow.environments.append(env)
                                    elif isinstance(env, dict) and "name" in env:
                                        workflow.environments.append(env["name"])

                    # Extract secrets from entire content
                    workflow.secrets_used = list(set(re.findall(r'\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}', content)))

            except Exception:
                pass

        # Fallback to regex if YAML failed or unavailable
        if not workflow.jobs:
            # Extract workflow name
            name_match = re.search(r'^name:\s*["\']?([^"\'\n]+)', content, re.MULTILINE)
            if name_match:
                workflow.name = name_match.group(1).strip()

            # Extract triggers (look for 'on:' section)
            # Handle both 'on: push' and 'on:\n  push:\n  pull_request:'
            simple_on = re.search(r'^on:\s*(\w+)\s*$', content, re.MULTILINE)
            if simple_on:
                workflow.triggers = [simple_on.group(1)]
            else:
                array_on = re.search(r'^on:\s*\[([^\]]+)\]', content, re.MULTILINE)
                if array_on:
                    workflow.triggers = [t.strip() for t in array_on.group(1).split(',')]
                else:
                    # Multi-line on: block - find triggers between 'on:' and 'jobs:'
                    on_block = re.search(r'^on:\s*\n(.*?)^jobs:', content, re.MULTILINE | re.DOTALL)
                    if on_block:
                        trigger_block = on_block.group(1)
                        # Triggers are at 2-space indent level
                        workflow.triggers = re.findall(r'^  ([a-z_]+):', trigger_block, re.MULTILINE)

            # Extract job names (under 'jobs:' section with 2-space indent)
            jobs_block = re.search(r'^jobs:\s*\n(.*?)(?:^[a-z]|\Z)', content, re.MULTILINE | re.DOTALL)
            if jobs_block:
                workflow.jobs = re.findall(r'^  ([a-zA-Z_][a-zA-Z0-9_-]*):', jobs_block.group(1), re.MULTILINE)

            # Extract secrets
            workflow.secrets_used = list(set(re.findall(r'\$\{\{\s*secrets\.([A-Z_][A-Z0-9_]*)\s*\}\}', content)))

            # Extract environments
            workflow.environments = list(set(re.findall(r'environment:\s*["\']?([a-zA-Z][a-zA-Z0-9_-]*)', content)))

        profile.ci_workflows.append(workflow)
        profile.detected_tools.append("github-actions")

    def _parse_gitlab_ci(self, ci_file: Path, profile: RepositoryProfile) -> None:
        """Parse GitLab CI configuration."""
        content = self._read_file_safe(ci_file)
        if not content:
            return

        workflow = CIWorkflow(
            name="GitLab CI",
            file_path=ci_file.relative_to(profile.root) if ci_file.is_relative_to(profile.root) else ci_file,
            platform="gitlab-ci",
        )

        # Extract stages
        stages_match = re.search(r'^stages:\s*\n((?:\s+-\s*.+\n)*)', content, re.MULTILINE)
        if stages_match:
            workflow.triggers = re.findall(r'-\s*(\w+)', stages_match.group(1))

        # Extract job names (lines that start with word and have a colon, excluding reserved words)
        reserved = {'stages', 'variables', 'include', 'default', 'workflow', 'image', 'services', 'before_script', 'after_script', 'cache'}
        for match in re.finditer(r'^([a-zA-Z_][a-zA-Z0-9_-]*):', content, re.MULTILINE):
            job = match.group(1)
            if job not in reserved and not job.startswith('.'):
                workflow.jobs.append(job)

        # Extract variables that look like secrets
        workflow.secrets_used = list(set(re.findall(r'\$([A-Z_]{3,})', content)))

        # Extract environments
        workflow.environments = list(set(re.findall(r'environment:\s*(?:name:\s*)?["\']?(\w+)', content)))

        profile.ci_workflows.append(workflow)
        profile.detected_tools.append("gitlab-ci")

    def _parse_jenkinsfile(self, jenkinsfile: Path, profile: RepositoryProfile) -> None:
        """Parse Jenkinsfile."""
        content = self._read_file_safe(jenkinsfile)
        if not content:
            return

        workflow = CIWorkflow(
            name="Jenkins Pipeline",
            file_path=jenkinsfile.relative_to(profile.root) if jenkinsfile.is_relative_to(profile.root) else jenkinsfile,
            platform="jenkins",
        )

        # Extract stages
        workflow.jobs = re.findall(r"stage\s*\(\s*['\"]([^'\"]+)['\"]", content)

        # Extract credentials/secrets
        workflow.secrets_used = list(set(re.findall(r"credentials\s*\(\s*['\"]([^'\"]+)['\"]", content)))

        # Extract environment
        workflow.environments = list(set(re.findall(r"environment\s*\{\s*\n.*?(\w+)\s*=", content, re.DOTALL)))

        profile.ci_workflows.append(workflow)
        profile.detected_tools.append("jenkins")

    def _parse_circleci(self, ci_file: Path, profile: RepositoryProfile) -> None:
        """Parse CircleCI configuration."""
        content = self._read_file_safe(ci_file)
        if not content:
            return

        workflow = CIWorkflow(
            name="CircleCI",
            file_path=ci_file.relative_to(profile.root) if ci_file.is_relative_to(profile.root) else ci_file,
            platform="circleci",
        )

        # Extract jobs
        jobs_section = re.search(r'^jobs:\s*\n((?:\s+.+\n)*)', content, re.MULTILINE)
        if jobs_section:
            workflow.jobs = re.findall(r'^  ([a-zA-Z_][a-zA-Z0-9_-]*):', jobs_section.group(1), re.MULTILINE)

        # Extract workflows
        workflows_match = re.findall(r'^  ([a-zA-Z_][a-zA-Z0-9_-]*):', content, re.MULTILINE)
        if workflows_match:
            workflow.triggers = workflows_match

        profile.ci_workflows.append(workflow)
        profile.detected_tools.append("circleci")

    def _extract_code_structure(self, root: Path, profile: RepositoryProfile) -> None:
        """Extract classes, functions, and imports from ALL code files."""
        for insight in profile.file_insights:
            if insight.language not in {"Python", "JavaScript", "TypeScript", "TypeScript React", "JavaScript React"}:
                continue

            full_path = root / insight.path
            content = self._read_file_safe(full_path)
            if not content:
                continue

            if insight.language == "Python":
                self._extract_python_structure(content, insight)
            elif insight.language in {"JavaScript", "TypeScript", "TypeScript React", "JavaScript React"}:
                self._extract_js_structure(content, insight)

    def _extract_python_structure(self, content: str, insight: FileInsight) -> None:
        """Extract Python classes, functions, imports, and docstrings."""
        from .models import CodeSymbol

        # Classes with docstrings: class ClassName(bases):\n    """docstring"""
        class_pattern = re.compile(
            r'^class\s+([A-Z][a-zA-Z0-9_]*)\s*(?:\(([^)]*)\))?\s*:'  # class Name(bases):
            r'(?:\s*\n\s*(?:"""([^"]*?)"""|\'\'\'([^\']*?)\'\'\'))?',  # optional docstring
            re.MULTILINE
        )
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            bases = match.group(2) or ""
            docstring = (match.group(3) or match.group(4) or "").strip()
            # Get first line of docstring
            docstring_first = docstring.split('\n')[0].strip() if docstring else ""

            # If no docstring, infer purpose from name
            if not docstring_first:
                docstring_first = self._infer_purpose_from_name(class_name, "class", bases=bases)

            insight.classes.append(class_name)
            insight.symbols.append(CodeSymbol(
                name=class_name,
                symbol_type="class",
                docstring=docstring_first[:200],  # Limit length
                signature=bases[:100] if bases else "",
                file_path=str(insight.path),
            ))

        # Functions with docstrings: def func_name(params):\n    """docstring"""
        func_pattern = re.compile(
            r'^def\s+([a-z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*(?:->.*?)?\s*:'  # def name(params):
            r'(?:\s*\n\s*(?:"""([^"]*?)"""|\'\'\'([^\']*?)\'\'\'))?',  # optional docstring
            re.MULTILINE
        )
        for match in func_pattern.finditer(content):
            func_name = match.group(1)
            params = match.group(2) or ""
            docstring = (match.group(3) or match.group(4) or "").strip()
            docstring_first = docstring.split('\n')[0].strip() if docstring else ""

            insight.functions.append(func_name)
            # Only add to symbols if it's a top-level function (not indented)
            # Check if the match starts at column 0
            line_start = content.rfind('\n', 0, match.start()) + 1
            if match.start() == line_start:  # Top-level function
                # If no docstring, infer purpose from name
                if not docstring_first:
                    docstring_first = self._infer_purpose_from_name(func_name, "function", params=params)

                insight.symbols.append(CodeSymbol(
                    name=func_name,
                    symbol_type="function",
                    docstring=docstring_first[:200],
                    signature=self._simplify_params(params),
                    file_path=str(insight.path),
                ))

        # Imports: from X import Y or import X
        for match in re.finditer(r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', content, re.MULTILINE):
            module = match.group(1) or match.group(2)
            if module and not module.startswith('_'):
                # Get the base module
                base = module.split('.')[0]
                if base not in insight.imports:
                    insight.imports.append(base)

    def _simplify_params(self, params: str) -> str:
        """Simplify function parameters for display."""
        if not params:
            return "()"
        # Remove type hints and defaults for brevity
        simplified = []
        for param in params.split(','):
            param = param.strip()
            if not param:
                continue
            # Get just the parameter name
            name = param.split(':')[0].split('=')[0].strip()
            if name and name != 'self' and name != 'cls':
                simplified.append(name)
        return f"({', '.join(simplified)})" if simplified else "()"

    def _infer_purpose_from_name(self, name: str, symbol_type: str, params: str = "", bases: str = "") -> str:
        """Infer what a class/function does from its name and signature when no docstring exists."""
        # Convert camelCase/PascalCase/snake_case to words
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)  # camelCase -> camel Case
        words = words.replace('_', ' ').lower().split()

        if not words:
            return ""

        # Common function prefixes and their meanings
        func_prefixes = {
            'get': 'Get',
            'set': 'Set',
            'is': 'Check if',
            'has': 'Check if has',
            'can': 'Check if can',
            'should': 'Determine if should',
            'create': 'Create',
            'build': 'Build',
            'make': 'Create',
            'init': 'Initialize',
            'setup': 'Set up',
            'configure': 'Configure',
            'load': 'Load',
            'save': 'Save',
            'read': 'Read',
            'write': 'Write',
            'parse': 'Parse',
            'format': 'Format',
            'convert': 'Convert',
            'transform': 'Transform',
            'validate': 'Validate',
            'check': 'Check',
            'verify': 'Verify',
            'process': 'Process',
            'handle': 'Handle',
            'run': 'Run',
            'execute': 'Execute',
            'start': 'Start',
            'stop': 'Stop',
            'send': 'Send',
            'receive': 'Receive',
            'fetch': 'Fetch',
            'update': 'Update',
            'delete': 'Delete',
            'remove': 'Remove',
            'add': 'Add',
            'insert': 'Insert',
            'find': 'Find',
            'search': 'Search',
            'filter': 'Filter',
            'sort': 'Sort',
            'merge': 'Merge',
            'split': 'Split',
            'extract': 'Extract',
            'generate': 'Generate',
            'render': 'Render',
            'display': 'Display',
            'show': 'Show',
            'hide': 'Hide',
            'enable': 'Enable',
            'disable': 'Disable',
            'register': 'Register',
            'unregister': 'Unregister',
            'subscribe': 'Subscribe to',
            'unsubscribe': 'Unsubscribe from',
            'connect': 'Connect to',
            'disconnect': 'Disconnect from',
            'open': 'Open',
            'close': 'Close',
            'reset': 'Reset',
            'clear': 'Clear',
            'refresh': 'Refresh',
            'sync': 'Synchronize',
            'async': 'Asynchronously process',
            'await': 'Wait for',
            'on': 'Handle event',
            'emit': 'Emit event',
            'trigger': 'Trigger',
            'dispatch': 'Dispatch',
            'apply': 'Apply',
            'resolve': 'Resolve',
            'reject': 'Reject',
            'throw': 'Throw',
            'catch': 'Catch',
            'try': 'Try to',
            'ensure': 'Ensure',
            'require': 'Require',
            'assert': 'Assert',
            'log': 'Log',
            'debug': 'Debug',
            'trace': 'Trace',
            'warn': 'Warn about',
            'error': 'Report error',
            'notify': 'Notify',
            'alert': 'Alert',
            'cache': 'Cache',
            'invalidate': 'Invalidate',
            'serialize': 'Serialize',
            'deserialize': 'Deserialize',
            'encode': 'Encode',
            'decode': 'Decode',
            'encrypt': 'Encrypt',
            'decrypt': 'Decrypt',
            'hash': 'Hash',
            'compress': 'Compress',
            'decompress': 'Decompress',
            'normalize': 'Normalize',
            'sanitize': 'Sanitize',
            'escape': 'Escape',
            'unescape': 'Unescape',
            'map': 'Map',
            'reduce': 'Reduce',
            'collect': 'Collect',
            'aggregate': 'Aggregate',
            'calculate': 'Calculate',
            'compute': 'Compute',
            'measure': 'Measure',
            'count': 'Count',
            'sum': 'Sum',
            'average': 'Calculate average of',
            'clone': 'Clone',
            'copy': 'Copy',
            'move': 'Move',
            'swap': 'Swap',
            'compare': 'Compare',
            'match': 'Match',
            'test': 'Test',
            'mock': 'Mock',
            'stub': 'Stub',
            'spy': 'Spy on',
            'patch': 'Patch',
            'wrap': 'Wrap',
            'unwrap': 'Unwrap',
            'bind': 'Bind',
            'unbind': 'Unbind',
            'attach': 'Attach',
            'detach': 'Detach',
            'mount': 'Mount',
            'unmount': 'Unmount',
            'inject': 'Inject',
            'provide': 'Provide',
            'expose': 'Expose',
            'publish': 'Publish',
            'broadcast': 'Broadcast',
            'listen': 'Listen for',
            'observe': 'Observe',
            'watch': 'Watch',
            'monitor': 'Monitor',
            'track': 'Track',
            'trace': 'Trace',
            'profile': 'Profile',
            'benchmark': 'Benchmark',
            'optimize': 'Optimize',
            'to': 'Convert to',
            'from': 'Create from',
            'as': 'Get as',
        }

        # Common class suffixes and their meanings
        class_suffixes = {
            'handler': 'Handles',
            'manager': 'Manages',
            'controller': 'Controls',
            'service': 'Provides service for',
            'provider': 'Provides',
            'factory': 'Creates',
            'builder': 'Builds',
            'parser': 'Parses',
            'converter': 'Converts',
            'transformer': 'Transforms',
            'validator': 'Validates',
            'serializer': 'Serializes',
            'deserializer': 'Deserializes',
            'encoder': 'Encodes',
            'decoder': 'Decodes',
            'adapter': 'Adapts',
            'wrapper': 'Wraps',
            'proxy': 'Proxies',
            'cache': 'Caches',
            'store': 'Stores',
            'repository': 'Repository for',
            'client': 'Client for',
            'server': 'Server for',
            'connection': 'Connection to',
            'connector': 'Connects to',
            'listener': 'Listens for',
            'observer': 'Observes',
            'watcher': 'Watches',
            'monitor': 'Monitors',
            'tracker': 'Tracks',
            'logger': 'Logs',
            'reporter': 'Reports',
            'notifier': 'Notifies',
            'dispatcher': 'Dispatches',
            'scheduler': 'Schedules',
            'executor': 'Executes',
            'runner': 'Runs',
            'worker': 'Worker for',
            'processor': 'Processes',
            'generator': 'Generates',
            'iterator': 'Iterates over',
            'loader': 'Loads',
            'reader': 'Reads',
            'writer': 'Writes',
            'stream': 'Streams',
            'buffer': 'Buffers',
            'queue': 'Queue for',
            'stack': 'Stack for',
            'pool': 'Pool of',
            'registry': 'Registry of',
            'catalog': 'Catalog of',
            'config': 'Configuration for',
            'settings': 'Settings for',
            'options': 'Options for',
            'context': 'Context for',
            'state': 'State of',
            'model': 'Data model for',
            'entity': 'Entity representing',
            'dto': 'Data transfer object for',
            'schema': 'Schema for',
            'spec': 'Specification for',
            'template': 'Template for',
            'view': 'View for',
            'component': 'Component for',
            'widget': 'Widget for',
            'element': 'Element for',
            'node': 'Node in',
            'tree': 'Tree structure for',
            'graph': 'Graph of',
            'list': 'List of',
            'set': 'Set of',
            'map': 'Map of',
            'dict': 'Dictionary of',
            'array': 'Array of',
            'collection': 'Collection of',
            'group': 'Group of',
            'batch': 'Batch of',
            'chunk': 'Chunk of',
            'page': 'Page of',
            'result': 'Result of',
            'response': 'Response from',
            'request': 'Request to',
            'message': 'Message for',
            'event': 'Event for',
            'action': 'Action for',
            'command': 'Command to',
            'query': 'Query for',
            'filter': 'Filter for',
            'rule': 'Rule for',
            'policy': 'Policy for',
            'strategy': 'Strategy for',
            'algorithm': 'Algorithm for',
            'helper': 'Helper for',
            'util': 'Utility for',
            'utils': 'Utilities for',
            'tool': 'Tool for',
            'mixin': 'Mixin providing',
            'trait': 'Trait providing',
            'interface': 'Interface for',
            'abstract': 'Abstract base for',
            'base': 'Base class for',
            'error': 'Error for',
            'exception': 'Exception for',
            'middleware': 'Middleware for',
            'plugin': 'Plugin for',
            'extension': 'Extension for',
            'hook': 'Hook for',
            'callback': 'Callback for',
            'decorator': 'Decorator for',
            'annotation': 'Annotation for',
            'test': 'Tests for',
            'mock': 'Mock for',
            'stub': 'Stub for',
            'fixture': 'Test fixture for',
            'evaluator': 'Evaluates',
            'retriever': 'Retrieves',
            'embedder': 'Embeds',
            'splitter': 'Splits',
            'extractor': 'Extracts',
            'analyzer': 'Analyzes',
            'scanner': 'Scans',
            'crawler': 'Crawls',
            'scraper': 'Scrapes',
            'fetcher': 'Fetches',
            'importer': 'Imports',
            'exporter': 'Exports',
            'migrator': 'Migrates',
            'installer': 'Installs',
            'deployer': 'Deploys',
            'orchestrator': 'Orchestrates',
            'coordinator': 'Coordinates',
            'mediator': 'Mediates',
            'broker': 'Brokers',
            'agent': 'Agent for',
            'bot': 'Bot for',
            'llm': 'Language model for',
        }

        if symbol_type == "function":
            # Check for common prefixes
            first_word = words[0]
            if first_word in func_prefixes:
                rest = ' '.join(words[1:]) if len(words) > 1 else ''
                desc = f"{func_prefixes[first_word]} {rest}".strip()
                return desc

            # If no known prefix, just humanize the name
            return ' '.join(words).capitalize()

        elif symbol_type == "class":
            # Check for Base/Abstract prefix FIRST
            if words[0] in ('base', 'abstract'):
                rest = ' '.join(words[1:]) if len(words) > 1 else 'functionality'
                return f"Abstract base class for {rest}"

            # Check for common suffixes
            last_word = words[-1]
            if last_word in class_suffixes:
                rest = ' '.join(words[:-1]) if len(words) > 1 else ''
                desc = f"{class_suffixes[last_word]} {rest}".strip()
                # Add base class info if present
                if bases:
                    first_base = bases.split(',')[0].strip()
                    if first_base and first_base not in ('object', 'ABC', 'BaseModel', 'Enum'):
                        desc += f" (extends {first_base})"
                return desc

            # If has base classes, mention it
            if bases:
                first_base = bases.split(',')[0].strip()
                if first_base and first_base not in ('object', 'ABC', 'BaseModel', 'Enum'):
                    return f"{' '.join(words).capitalize()} (extends {first_base})"

            # Just humanize the name
            return ' '.join(words).capitalize()

        elif symbol_type == "interface":
            rest = ' '.join(words)
            return f"Interface defining {rest}"

        return ""

    def _extract_js_structure(self, content: str, insight: FileInsight) -> None:
        """Extract JavaScript/TypeScript classes, functions, imports, and JSDoc comments."""
        from .models import CodeSymbol

        # First, build a map of JSDoc comments to their positions
        # This allows us to find the JSDoc that precedes each definition
        jsdoc_map: dict[int, str] = {}  # end_position -> jsdoc_content
        for match in re.finditer(r'/\*\*\s*(.*?)\s*\*/', content, re.DOTALL):
            jsdoc_content = match.group(1)
            # Extract first meaningful line from JSDoc
            jsdoc_desc = ""
            lines = [l.strip().lstrip('*').strip() for l in jsdoc_content.split('\n')]
            for line in lines:
                if line and not line.startswith('@'):
                    jsdoc_desc = line[:200]
                    break
            if jsdoc_desc:
                jsdoc_map[match.end()] = jsdoc_desc

        def find_preceding_jsdoc(pos: int) -> str:
            """Find JSDoc comment that ends just before this position."""
            # Look for JSDoc that ends within 50 chars before this position
            for end_pos, desc in jsdoc_map.items():
                # Check if there's only whitespace between JSDoc end and definition
                between = content[end_pos:pos].strip()
                if not between or between in ('export', 'export default', 'async'):
                    return desc
            return ""

        # Classes
        class_pattern = re.compile(
            r'(?:export\s+(?:default\s+)?)?class\s+([A-Z][a-zA-Z0-9_]*)'
            r'(?:\s+extends\s+([A-Z][a-zA-Z0-9_]*))?'
        )
        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            extends = match.group(2) or ""
            jsdoc_desc = find_preceding_jsdoc(match.start())

            # If no JSDoc, infer purpose from name
            if not jsdoc_desc:
                jsdoc_desc = self._infer_purpose_from_name(class_name, "class", bases=extends)

            insight.classes.append(class_name)
            insight.symbols.append(CodeSymbol(
                name=class_name,
                symbol_type="class",
                docstring=jsdoc_desc,
                signature=f"extends {extends}" if extends else "",
                file_path=str(insight.path),
            ))

        # Functions
        func_pattern = re.compile(
            r'(?:export\s+(?:default\s+)?)?(?:async\s+)?'
            r'(?:function\s+([a-z][a-zA-Z0-9_]*)|'
            r'(?:const|let|var)\s+([a-z][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)'
        )
        for match in func_pattern.finditer(content):
            func_name = match.group(1) or match.group(2)
            if not func_name:
                continue

            jsdoc_desc = find_preceding_jsdoc(match.start())

            # If no JSDoc, infer purpose from name
            if not jsdoc_desc:
                jsdoc_desc = self._infer_purpose_from_name(func_name, "function")

            if func_name not in insight.functions:
                insight.functions.append(func_name)
                insight.symbols.append(CodeSymbol(
                    name=func_name,
                    symbol_type="function",
                    docstring=jsdoc_desc,
                    signature="",
                    file_path=str(insight.path),
                ))

        # TypeScript interfaces and types
        interface_pattern = re.compile(
            r'(?:export\s+)?(?:interface|type)\s+([A-Z][a-zA-Z0-9_]*)'
        )
        for match in interface_pattern.finditer(content):
            type_name = match.group(1)
            jsdoc_desc = find_preceding_jsdoc(match.start())

            # If no JSDoc, infer purpose from name
            if not jsdoc_desc:
                jsdoc_desc = self._infer_purpose_from_name(type_name, "interface")

            if type_name not in insight.classes:
                insight.classes.append(type_name)
                insight.symbols.append(CodeSymbol(
                    name=type_name,
                    symbol_type="interface",
                    docstring=jsdoc_desc,
                    signature="",
                    file_path=str(insight.path),
                ))

        # Imports
        for match in re.finditer(r'import\s+.*?from\s+[\'"]([^"\']+)[\'"]', content):
            module = match.group(1).split('/')[0].lstrip('@')
            if module and module not in insight.imports:
                insight.imports.append(module)

    def _build_directory_summaries(self, profile: RepositoryProfile) -> None:
        """Build summaries for each directory showing complete structure."""
        from collections import defaultdict

        # Group files by directory
        dir_files: dict[str, list[FileInsight]] = defaultdict(list)
        for insight in profile.file_insights:
            # Get directory path (up to 2 levels deep for grouping)
            parts = insight.path.parts
            if len(parts) > 2:
                dir_key = str(Path(*parts[:2]))
            elif len(parts) > 1:
                dir_key = str(parts[0])
            else:
                dir_key = "root"
            dir_files[dir_key].append(insight)

        # Build summary for each directory
        for dir_path, files in sorted(dir_files.items()):
            languages: dict[str, int] = {}
            categories: dict[str, int] = {}
            all_classes: list[str] = []
            all_functions: list[str] = []
            key_files: list[str] = []
            all_symbols: list = []

            for f in files:
                languages[f.language] = languages.get(f.language, 0) + 1
                categories[f.category] = categories.get(f.category, 0) + 1
                all_classes.extend(f.classes[:10])  # Limit per file
                all_functions.extend(f.functions[:10])
                # Collect symbols with docstrings (prioritize those with descriptions)
                all_symbols.extend(f.symbols)
                if f.importance_score >= 0.3 or f.is_entry_point:
                    key_files.append(str(f.path))

            # Sort symbols: those with docstrings first, then by name
            all_symbols.sort(key=lambda s: (not s.docstring, s.name))

            # Infer description based on directory name and contents
            description = self._infer_directory_purpose(dir_path, files)

            profile.directory_summaries.append(DirectorySummary(
                path=dir_path,
                file_count=len(files),
                languages=languages,
                categories=categories,
                key_files=key_files[:10],
                all_classes=list(set(all_classes))[:30],  # Dedupe and limit
                all_functions=list(set(all_functions))[:30],
                description=description,
                symbols=all_symbols[:50],  # Top 50 symbols per directory
            ))

    def _infer_directory_purpose(self, dir_path: str, files: list[FileInsight]) -> str:
        """Infer the purpose of a directory from its name and contents."""
        dir_lower = dir_path.lower()

        purposes = {
            "test": "Test files",
            "spec": "Test specifications",
            "src": "Source code",
            "lib": "Library code",
            "app": "Application code",
            "api": "API endpoints",
            "models": "Data models",
            "views": "View components",
            "components": "UI components",
            "hooks": "React hooks",
            "utils": "Utility functions",
            "helpers": "Helper functions",
            "services": "Service layer",
            "controllers": "Controllers",
            "routes": "Route definitions",
            "middleware": "Middleware",
            "config": "Configuration",
            "scripts": "Build/automation scripts",
            "docs": "Documentation",
            "examples": "Example code",
            "tools": "Tool implementations",
            "nodes": "Node components",
            "agents": "Agent implementations",
            "connections": "Connection handlers",
            "prompts": "Prompt templates",
            "memory": "Memory/storage",
            "retrievers": "RAG retrievers",
        }

        for key, purpose in purposes.items():
            if key in dir_lower:
                return purpose

        # Infer from file categories
        categories = [f.category for f in files]
        if categories:
            most_common = max(set(categories), key=categories.count)
            return f"{most_common.title()} files"

        return "General files"

    def _cache_important_files(self, root: Path, profile: RepositoryProfile) -> None:
        """Cache important files with smart prioritization and size management."""
        # Sort by importance score
        sorted_files = sorted(
            profile.file_insights,
            key=lambda f: f.importance_score,
            reverse=True,
        )

        # Prioritize specific file types for better context
        priority_files: list[str] = []

        # Always include these if they exist
        must_have = [
            "README.md", "readme.md", "README.rst",
            "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
            "Makefile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".env.example", ".env.sample",
        ]

        for insight in profile.file_insights:
            if insight.path.name in must_have:
                priority_files.append(str(insight.path))

        # Add entry points
        for insight in sorted_files:
            if insight.is_entry_point and str(insight.path) not in priority_files:
                priority_files.append(str(insight.path))

        # Add example files (valuable for understanding usage)
        example_files = [
            f for f in sorted_files
            if f.category == "examples" and f.language == "Python"
        ][:5]
        for f in example_files:
            if str(f.path) not in priority_files:
                priority_files.append(str(f.path))

        # Add core application files
        app_files = [
            f for f in sorted_files
            if f.category == "application" and f.importance_score >= 0.3
        ][:10]
        for f in app_files:
            if str(f.path) not in priority_files:
                priority_files.append(str(f.path))

        # Fill remaining slots with high-importance files
        for insight in sorted_files:
            if len(priority_files) >= self.max_important_files:
                break
            if str(insight.path) not in priority_files:
                priority_files.append(str(insight.path))

        # Cache files respecting total context limit
        total_size = 0
        for rel_path in priority_files:
            if total_size >= self.max_total_context_size:
                break
            full_path = root / rel_path
            content = self._read_file_safe(full_path)
            if content:
                # Truncate individual files if too large
                truncated = content[:self.max_file_content_size]
                profile.important_file_contents[rel_path] = truncated
                total_size += len(truncated)
