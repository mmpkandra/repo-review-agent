from __future__ import annotations

import os
from pathlib import Path

from .models import DocumentationArtifact, RepositoryProfile


# Document-specific generation prompts
DOC_PROMPTS = {
    "REPOSITORY_OVERVIEW": """Generate a comprehensive repository overview that includes:
- A clear "What This Repository Does" section explaining the purpose in 2-3 sentences
- An "At a Glance" table with key metrics (files, language, version, license)
- Technology stack and key dependencies organized by category
- Entry points with actual commands
- Architecture overview with directory structure
- Key concepts that developers need to understand
- Getting started commands based on the detected package manager

Use the repository evidence to extract real values. Include ASCII diagrams where helpful.""",

    "ARCHITECTURE_GUIDE": """Generate a detailed architecture guide that includes:
- Component architecture diagram (ASCII art showing relationships)
- Directory structure with explanations of each major folder's responsibility
- Data flow diagrams showing how information moves through the system
- Key components/classes WITH DESCRIPTIONS of what each does (not just names)
- Integration points and extension mechanisms
- Design patterns used in the codebase

IMPORTANT FOR CLASSES AND FUNCTIONS:
- Don't just list names - explain what each class/function DOES
- Group related classes together and explain their relationships
- Show how key classes interact with each other
- Include example usage or key methods for important classes

FOR INFRASTRUCTURE REPOS (Terraform, Ansible, Helm, K8s):
- Infrastructure topology diagram (regions, VPCs, subnets, services)
- Module/role dependency graph
- Resource relationships and state management
- Provider configurations and required permissions
- Naming conventions and tagging strategies

Base all content on actual code structure observed in the evidence. Include code snippets showing key patterns.""",

    "CONFIGURATION_GUIDE": """Generate a comprehensive configuration guide that includes:
- Environment variables table with: name, required/optional, default value, description
- Group variables by category (AI providers, databases, tools, etc.)
- Configuration files section explaining each config file's purpose
- Quick setup section with copy-pasteable commands
- Provider-specific notes for different services

FOR INFRASTRUCTURE REPOS:
- Terraform variables (variables.tf) with descriptions and defaults
- Terraform outputs and their purposes
- Backend configuration (S3, GCS, Azure Blob, etc.)
- Provider authentication requirements (AWS, GCP, Azure credentials)
- Ansible inventory and group_vars structure
- Helm values.yaml parameters by category
- Environment-specific overrides (dev, staging, prod)

Extract actual variable names and defaults from the evidence.""",

    "DEPLOYMENT_RUNBOOK": """Generate a production-ready deployment runbook that includes:
- Prerequisites with exact version requirements
- Step-by-step deployment for: local, Docker, and production (K8s if applicable)
- Working Docker commands based on detected Dockerfile
- Environment setup checklist
- Rollback procedures with actual commands
- Health check commands and endpoints
- Post-deployment verification checklist

CI/CD AUTOMATED DEPLOYMENT (summary only - details in QUALITY_AND_VALIDATION):
- How deployments are triggered (which workflows, which branches)
- Environment promotion flow (dev -> staging -> prod)
- How to manually trigger deployments
- Rollback via CI/CD (revert commit, re-run previous workflow)

NOTE: For full CI/CD pipeline details (jobs, secrets, triggers), refer to QUALITY_AND_VALIDATION.
This section focuses on the deployment PROCESS, not pipeline configuration.

FOR INFRASTRUCTURE REPOS:
- Terraform workflow: init, plan, apply, destroy
- State management and locking procedures
- Multi-environment deployment (dev -> staging -> prod)
- Terraform workspaces or directory-based environments
- Ansible playbook execution order and tags
- Helm install/upgrade/rollback commands
- Drift detection and reconciliation
- Disaster recovery procedures

Include real commands based on the detected tools.""",

    "OPERATIONS_RUNBOOK": """Generate an operations runbook that includes:
- Available commands table (from Makefile, package.json scripts, etc.)
- Service start/stop/restart commands
- Log locations and how to access them
- Troubleshooting table with: symptom, cause, resolution
- Performance monitoring commands
- Common maintenance tasks
- Debug mode instructions

FOR INFRASTRUCTURE REPOS:
- Terraform state inspection and manipulation commands
- Resource import and state mv procedures
- Taint/untaint for resource recreation
- Ansible ad-hoc commands for quick fixes
- kubectl commands for K8s troubleshooting
- Log aggregation and monitoring (CloudWatch, Stackdriver, Azure Monitor)
- Cost management and resource cleanup
- Security group and IAM debugging
- Certificate renewal procedures

Extract actual commands from Makefile, scripts, or other automation files.""",

    "API_REFERENCE": """Generate an API reference that includes:
- Endpoints table with: method, path, description, source file
- Authentication patterns if detected
- Request/response examples based on code patterns
- Code examples showing how to build APIs with this framework
- WebSocket endpoints if applicable
- Error handling patterns

Base examples on actual route decorators and handlers found in the code.""",

    "QUALITY_AND_VALIDATION": """Generate a quality and validation guide that includes:
- Test structure overview (unit, integration, e2e)
- Commands to run different test types
- Test fixtures and how to use them
- Mocking patterns used in the codebase
- Coverage targets and how to generate reports
- Pre-commit hooks and linting tools

CI/CD PIPELINE SECTION (THIS IS THE PRIMARY LOCATION FOR CI/CD INFO):
This document is the authoritative source for CI/CD pipeline documentation.
Include comprehensive details about:
- Pipeline overview diagram showing workflow stages
- Trigger conditions (push, PR, schedule, manual)
- Jobs and their purposes - explain what each job does
- Quality gates and checks performed
- Required secrets and how to configure them
- Deployment environments and promotion flow
- How to debug failed workflows
- Branch protection rules implied by the workflows

FOR INFRASTRUCTURE REPOS:
- Terraform validation and formatting (terraform validate, terraform fmt)
- Terraform plan review process
- tflint, tfsec, checkov, or other IaC security scanning
- Terratest or kitchen-terraform for integration tests
- Ansible-lint and molecule testing
- Helm lint and template validation
- Policy as Code (OPA, Sentinel, Conftest)
- Cost estimation tools (Infracost)
- Compliance scanning (Prowler, ScoutSuite)

Extract actual test commands, workflow details, and patterns from the evidence.""",

    "USAGE_PATTERNS": """Generate a usage patterns guide with WORKING CODE EXAMPLES:
- Basic usage example (simplest possible working code)
- Common workflow examples
- Integration patterns
- Advanced usage patterns
- Anti-patterns to avoid
- Best practices

IMPORTANT: Generate realistic, runnable code examples based on the imports and patterns
visible in the example files. Use the actual API from the codebase.""",

    "DEVELOPER_WORKFLOWS": """Generate a developer workflows guide that includes:
- Initial setup steps with exact commands
- Development workflow (branch, code, test, commit, PR)
- Code style guidelines based on detected linters
- How to add new features (with file locations)
- Debugging tips
- Common tasks (update deps, run specific tests, etc.)

GITHUB REPOSITORY CONFIGURATION (THIS IS THE PRIMARY LOCATION):
This document is the authoritative source for GitHub config documentation.
Include comprehensive details about:
- Code ownership: who owns what paths (from CODEOWNERS)
- Issue templates: how to file bugs, feature requests
- PR template: what to include in pull requests
- Branch protection: which branches are protected
- Dependabot: automated dependency updates
- Release process: how releases are drafted/published
- Custom actions: reusable workflows available
- Required checks: what CI jobs must pass

NOTE: Do NOT duplicate full CI/CD pipeline details here - refer to QUALITY_AND_VALIDATION
for pipeline details. Only mention CI/CD in the context of the developer workflow.

Use actual tool names, commands, and GitHub config from the evidence.""",

    "GETTING_STARTED": """Generate a getting started guide that includes:
- Prerequisites with versions
- Installation steps (multiple methods if available)
- First working example (minimal code to verify setup)
- Next steps and links to other docs
- Common issues during setup and solutions

Make the first example actually runnable based on the codebase patterns.""",
}

SYSTEM_INSTRUCTION = """You are an expert technical writer generating documentation for software repositories.

CRITICAL RULES:
1. Generate WORKING code examples based on actual imports and patterns in the evidence
2. Use real file paths, commands, and configurations from the evidence
3. Create ASCII diagrams for architecture when helpful
4. Include tables for structured data (env vars, commands, endpoints)
5. Be specific - use actual names, versions, and values from the evidence
6. If information is missing, say "Requires documentation" rather than inventing
7. Format output as clean, professional Markdown
8. Include practical, copy-pasteable commands
9. DO NOT include raw data dumps, JSON, or "Repository Evidence" sections in the output
10. DO NOT just list class/function names - explain what they do and how they relate
11. DO NOT include sections that don't apply (e.g., Terraform for non-infra repos)
12. DO NOT repeat information across sections - keep content focused and unique
13. ALWAYS generate COMPLETE sections - never truncate or summarize prematurely"""


# Model mappings for different providers
# Updated: April 2026 - based on available Bedrock models
# Note: Most newer models require inference profiles (us. prefix for cross-region)
BEDROCK_MODELS = {
    # Claude 4.x models - require inference profiles
    "claude-sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",  # Claude 4.5 Sonnet
    "claude-haiku": "us.anthropic.claude-haiku-4-5-20251001-v1:0",    # Claude 4.5 Haiku
    "claude-opus": "us.anthropic.claude-opus-4-5-20251101-v1:0",      # Claude 4.5 Opus
    "claude-4-sonnet": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claude-4-haiku": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-4-opus": "us.anthropic.claude-opus-4-5-20251101-v1:0",
    # Claude 3.7 Sonnet - requires inference profile
    "claude-3.7-sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    # Claude 3.5 Haiku - requires inference profile
    "claude-3.5-haiku": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    # Claude 3.x legacy models - direct invocation still works
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    # Amazon Titan
    "titan-text": "amazon.titan-text-premier-v1:0",
    # Llama
    "llama3-70b": "meta.llama3-70b-instruct-v1:0",
    "llama3-8b": "meta.llama3-8b-instruct-v1:0",
    # Mistral
    "mistral-large": "mistral.mistral-large-2402-v1:0",
}


class OpenAIDocRefiner:
    """AI-powered documentation refinement with document-specific strategies."""

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4.1-mini",
        aws_region: str | None = None,
        aws_profile: str | None = None,
        aws_role_arn: str | None = None,
        max_input_files: int = 25,
        max_file_chars: int = 15000,
        verbose: bool = True,  # Show progress
    ) -> None:
        self.provider = provider
        self.model = model
        self.aws_region = aws_region
        self.aws_profile = aws_profile  # AWS CLI profile name
        self.aws_role_arn = aws_role_arn  # IAM role to assume
        self.max_input_files = max_input_files
        self.max_file_chars = max_file_chars
        self.verbose = verbose

    def _log(self, message: str, end: str = "\n") -> None:
        """Print progress message if verbose mode is enabled."""
        if self.verbose:
            print(message, end=end, flush=True)

    def is_configured(self) -> bool:
        if self.provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        if self.provider == "bedrock":
            # Bedrock uses IAM auth - check for any valid credential source
            # Will work with: env vars, ~/.aws/credentials, IAM role, instance profile
            return self._check_aws_credentials()
        return False

    def _check_aws_credentials(self) -> bool:
        """Check if AWS credentials are available for Bedrock."""
        # Check explicit environment variables
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            return True
        # Check for AWS profile
        if self.aws_profile or os.getenv("AWS_PROFILE"):
            return True
        # Check for role ARN (will be assumed)
        if self.aws_role_arn or os.getenv("AWS_ROLE_ARN"):
            return True
        # Check for default credentials file
        creds_file = Path.home() / ".aws" / "credentials"
        if creds_file.exists():
            return True
        # Check for EC2 instance profile / ECS task role / Lambda role
        # These are detected at runtime by boto3
        return True  # Let boto3 handle credential discovery

    def analyze_repository_semantics(self, profile: RepositoryProfile) -> None:
        """Deep semantic analysis of the repository."""
        if not self.is_configured():
            return

        self._log(f"[1/2] Analyzing repository semantics...", end=" ")

        try:
            client = self._build_client()
        except RuntimeError:
            self._log("SKIPPED (no credentials)")
            return

        repo_context = self._build_repo_context(profile)
        prompt = f"""Analyze this repository deeply and provide:

1. PURPOSE: A 2-3 sentence summary of what this repository does, who it's for, and what problems it solves.

2. ARCHITECTURE: Describe the high-level architecture including:
   - Main components and their responsibilities
   - How data flows through the system
   - Key design patterns used

3. CONCEPTS: List 5-7 key concepts/terms someone must understand to work with this codebase.

4. TECH_STACK: List the core technologies, frameworks, and tools used.

5. GETTING_STARTED: The minimal steps to get this running locally.

Repository context:
{repo_context}

Respond in this exact format (keep each section concise but informative):
PURPOSE: <summary>
ARCHITECTURE: <architecture description>
CONCEPTS: <comma-separated list>
TECH_STACK: <comma-separated list>
GETTING_STARTED: <numbered steps>"""

        try:
            text = self._call_llm(client, prompt, "Analyze the repository thoroughly.")
            self._log("DONE")

            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("PURPOSE:"):
                    profile.purpose_summary = line.replace("PURPOSE:", "").strip()
                elif line.startswith("ARCHITECTURE:"):
                    profile.architecture_summary = line.replace("ARCHITECTURE:", "").strip()
                elif line.startswith("CONCEPTS:"):
                    concepts = line.replace("CONCEPTS:", "").strip()
                    profile.key_concepts = [c.strip() for c in concepts.split(",") if c.strip()]
        except Exception as e:
            self._log(f"FAILED ({e})")

    def refine_artifacts(
        self,
        profile: RepositoryProfile,
        artifacts: list[DocumentationArtifact],
    ) -> list[DocumentationArtifact]:
        client = self._build_client()
        repo_context = self._build_repo_context(profile)
        refined: list[DocumentationArtifact] = []

        total = len(artifacts)
        self._log(f"[2/2] Generating {total} documents with AI...")

        for idx, artifact in enumerate(artifacts, 1):
            self._log(f"      [{idx}/{total}] {artifact.title}...", end=" ")
            try:
                refined_body = self._refine_body(client, profile, artifact, repo_context)
                refined.append(
                    DocumentationArtifact(
                        filename=artifact.filename,
                        title=artifact.title,
                        body=refined_body,
                        generated_with_ai=True,
                    )
                )
                self._log("DONE")
            except Exception as e:
                self._log(f"FAILED ({e})")
                # Keep original artifact on failure
                refined.append(artifact)

        return refined

    def _refine_body(
        self,
        client,
        profile: RepositoryProfile,
        artifact: DocumentationArtifact,
        repo_context: str,
    ) -> str:
        doc_type = artifact.filename.replace(".md", "")
        specific_prompt = DOC_PROMPTS.get(doc_type, "Generate comprehensive documentation.")

        # Estimate context size and decide on splitting strategy
        # Rough estimate: 1 token ≈ 4 characters for English text
        full_context_chars = len(repo_context) + len(artifact.body) + len(specific_prompt)
        estimated_input_tokens = full_context_chars // 4

        # If input is large, use chunked generation to avoid truncation
        # Most Claude models have 200k input limit but we want focused, quality output
        # Use chunking when estimated input > 50k tokens to ensure quality
        if estimated_input_tokens > 50000:
            return self._refine_body_chunked(
                client, profile, artifact, repo_context, doc_type, specific_prompt
            )

        prompt = f"""# Task: Generate {artifact.title}

## Document-Specific Instructions
{specific_prompt}

## Repository Context
- Name: {profile.name}
- Purpose: {profile.purpose_summary or 'Not yet analyzed'}
- Architecture: {profile.architecture_summary or 'Not yet analyzed'}
- Key Concepts: {', '.join(profile.key_concepts) if profile.key_concepts else 'Not yet analyzed'}

## Base Draft (enhance and expand this)
{artifact.body}

## Repository Evidence
{repo_context}

## Output
Generate the complete document in Markdown format. Make it production-ready.
IMPORTANT: Generate COMPLETE content. Do not truncate or summarize at the end."""

        try:
            text = self._call_llm(client, prompt, SYSTEM_INSTRUCTION)
        except Exception as exc:
            raise RuntimeError(self._format_error(exc)) from exc

        if not text:
            raise RuntimeError(f"LLM response for {artifact.filename} was empty.")

        # Post-process to clean up any raw data dumps
        text = self._clean_generated_content(text)
        return text

    def _clean_generated_content(self, text: str) -> str:
        """Remove raw data dumps and clean up generated content."""
        import re

        # Remove LLM context sections that shouldn't appear in final output
        # These are meant for the LLM to read, not for the final document
        context_section_patterns = [
            r"^#\s*CI/CD WORKFLOWS\s*\n.*?(?=^#[^#]|\Z)",  # # CI/CD WORKFLOWS section
            r"^#\s*GITHUB REPOSITORY CONFIGURATION\s*\n.*?(?=^#[^#]|\Z)",  # # GITHUB REPOSITORY CONFIGURATION
            r"^#\s*COMPLETE CODEBASE STRUCTURE\s*\n.*?(?=^#[^#]|\Z)",  # # COMPLETE CODEBASE STRUCTURE
            r"^#\s*ALL FILES IN REPOSITORY\s*\n.*?(?=^#[^#]|\Z)",  # # ALL FILES IN REPOSITORY
            r"^#\s*KEY FILE CONTENTS\s*\n.*?(?=^#[^#]|\Z)",  # # KEY FILE CONTENTS
        ]
        for pattern in context_section_patterns:
            text = re.sub(pattern, "", text, flags=re.MULTILINE | re.DOTALL)

        # Remove "Repository Evidence" sections that might have been included
        text = re.sub(
            r"##?\s*Repository Evidence.*?(?=^#|\Z)",
            "",
            text,
            flags=re.MULTILINE | re.DOTALL | re.IGNORECASE
        )

        # Remove raw JSON dumps (large objects)
        text = re.sub(
            r"```json\n\{[^}]{500,}\}\n```",
            "*[Structured data available in source files]*",
            text,
            flags=re.DOTALL
        )

        # Remove sections that just dump lists without explanation
        # (e.g., "Languages: {'Python': 836, 'YAML': 50...}")
        text = re.sub(
            r"^\s*Languages:\s*\{[^}]+\}\s*$",
            "",
            text,
            flags=re.MULTILINE
        )
        text = re.sub(
            r"^\s*Categories:\s*\{[^}]+\}\s*$",
            "",
            text,
            flags=re.MULTILINE
        )
        text = re.sub(
            r"^\s*Tools:\s*\[[^\]]+\]\s*$",
            "",
            text,
            flags=re.MULTILINE
        )
        text = re.sub(
            r"^\s*Purpose:\s*\w+\s+files\s*$",
            "",
            text,
            flags=re.MULTILINE
        )

        # Remove raw directory dumps like "## dynamiq/cache/ (10 files)" without context
        text = re.sub(
            r"^##\s+[\w/]+/\s*\(\d+\s+files?\)\s*\n\s+Purpose:.*?(?=^##|\Z)",
            "",
            text,
            flags=re.MULTILINE | re.DOTALL
        )

        # Remove inapplicable infrastructure sections for non-infra repos
        # (These patterns indicate the section was generated but has no real content)
        infra_patterns = [
            r"##?\s*Terraform.*?(?:not currently|not applicable|N/A|no terraform).*?(?=^#|\Z)",
            r"##?\s*Ansible.*?(?:not currently|not applicable|N/A|no ansible).*?(?=^#|\Z)",
            r"##?\s*Helm.*?(?:not currently|not applicable|N/A|no helm).*?(?=^#|\Z)",
            r"##?\s*Kubernetes.*?(?:not currently|not applicable|N/A|no kubernetes).*?(?=^#|\Z)",
        ]
        for pattern in infra_patterns:
            text = re.sub(pattern, "", text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

        # Clean up multiple consecutive blank lines
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        return text.strip()

    def _refine_body_chunked(
        self,
        client,
        profile: RepositoryProfile,
        artifact: DocumentationArtifact,
        repo_context: str,
        doc_type: str,
        specific_prompt: str,
    ) -> str:
        """Generate document in chunks to handle large context and avoid truncation."""
        # Split the generation into logical sections based on document type
        sections = self._get_doc_sections(doc_type)

        # Build a condensed context (exclude verbose file contents for section generation)
        condensed_context = self._build_condensed_context(profile, repo_context)

        generated_sections: list[str] = []
        total_sections = len(sections)

        for idx, section in enumerate(sections, 1):
            section_name = section["name"]
            section_instructions = section["instructions"]

            section_prompt = f"""# Task: Generate the "{section_name}" section for {artifact.title}

## Section-Specific Instructions
{section_instructions}

## Document Context
This is section {idx} of {total_sections} for the {artifact.title} document.
- Repository: {profile.name}
- Purpose: {profile.purpose_summary or 'Not yet analyzed'}
- Architecture: {profile.architecture_summary or 'Not yet analyzed'}

## Relevant Repository Data
{condensed_context}

## Previously Generated Sections
{self._summarize_previous_sections(generated_sections) if generated_sections else 'This is the first section.'}

## Output
Generate ONLY the "{section_name}" section content.
Start with the section header (## {section_name}).
Be thorough and complete. Do not truncate."""

            try:
                section_text = self._call_llm(client, section_prompt, SYSTEM_INSTRUCTION)
                if section_text:
                    generated_sections.append(section_text)
            except Exception:
                # On failure, generate a placeholder
                generated_sections.append(f"## {section_name}\n\n*Content generation failed. Requires manual documentation.*")

        # Combine all sections with document title
        combined = f"# {artifact.title}\n\n" + "\n\n".join(generated_sections)

        # Post-process to clean up any raw data dumps
        combined = self._clean_generated_content(combined)
        return combined

    def _get_doc_sections(self, doc_type: str) -> list[dict]:
        """Define logical sections for each document type."""
        sections_map = {
            "REPOSITORY_OVERVIEW": [
                {"name": "What This Repository Does", "instructions": "Write a clear 2-3 sentence summary of the repository's purpose, target audience, and key value proposition."},
                {"name": "At a Glance", "instructions": "Create a table with key metrics: total files, primary language, version (if found), license. Include technology stack."},
                {"name": "Key Dependencies", "instructions": "List and categorize the important dependencies. Group by purpose (e.g., AI/ML, Web Framework, Database, etc.)"},
                {"name": "Entry Points and Commands", "instructions": "Document how to start/run the application. Include actual commands from Makefile or package.json."},
                {"name": "Directory Structure", "instructions": "Explain the high-level directory structure and what each major folder contains."},
                {"name": "Getting Started", "instructions": "Provide quick start commands based on the detected package manager and tools."},
            ],
            "ARCHITECTURE_GUIDE": [
                {"name": "Overview", "instructions": "Describe the overall architecture in 2-3 paragraphs. Include an ASCII diagram if helpful."},
                {"name": "Component Architecture", "instructions": "List and describe each major component/module, its responsibility. For key classes, explain WHAT they do (not just their names). Group related classes and show relationships."},
                {"name": "Key Classes and Functions", "instructions": "Document the most important classes and functions with descriptions of their PURPOSE and HOW they work. Include key methods and usage examples."},
                {"name": "Directory Structure Details", "instructions": "Explain what each directory contains and its role in the architecture."},
                {"name": "Data Flow", "instructions": "Describe how data flows through the system. Include a flow diagram if helpful."},
                {"name": "Design Patterns", "instructions": "Identify and explain design patterns used in the codebase with examples."},
                {"name": "Integration Points", "instructions": "Document external integrations, APIs, and extension mechanisms."},
            ],
            "CONFIGURATION_GUIDE": [
                {"name": "Environment Variables", "instructions": "Create a comprehensive table of ALL environment variables with: name, required/optional, default, description. Group by category."},
                {"name": "Configuration Files", "instructions": "List and explain each configuration file (e.g., .env, config.yaml, etc.) and its purpose."},
                {"name": "Provider Configuration", "instructions": "Document provider-specific settings (AI providers, databases, cloud services, etc.)"},
                {"name": "Quick Setup", "instructions": "Provide copy-pasteable commands and example configurations to get started quickly."},
            ],
            "DEPLOYMENT_RUNBOOK": [
                {"name": "Prerequisites", "instructions": "List all prerequisites with exact version requirements."},
                {"name": "Local Deployment", "instructions": "Step-by-step guide for running locally."},
                {"name": "Docker Deployment", "instructions": "Instructions for Docker-based deployment. Include actual docker commands."},
                {"name": "Production Deployment", "instructions": "Production deployment guide including infrastructure requirements."},
                {"name": "CI/CD Integration", "instructions": "Document how deployments are automated via CI/CD pipelines."},
                {"name": "Rollback Procedures", "instructions": "Document how to rollback a failed deployment."},
                {"name": "Health Checks", "instructions": "List health check endpoints and verification steps."},
            ],
            "OPERATIONS_RUNBOOK": [
                {"name": "Available Commands", "instructions": "Create a table of all available commands (from Makefile, scripts, etc.) with descriptions."},
                {"name": "Service Operations", "instructions": "Document start, stop, restart, and status check procedures."},
                {"name": "Troubleshooting", "instructions": "Create a troubleshooting table with: symptom, possible cause, and resolution."},
                {"name": "Log Management", "instructions": "Document log locations and how to access/analyze logs."},
                {"name": "Performance Monitoring", "instructions": "Document monitoring tools and commands."},
                {"name": "Maintenance Tasks", "instructions": "Document common maintenance procedures."},
            ],
            "API_REFERENCE": [
                {"name": "Endpoints Overview", "instructions": "Create a table of all API endpoints with: method, path, description, source file."},
                {"name": "Authentication", "instructions": "Document authentication methods and patterns."},
                {"name": "Endpoint Details", "instructions": "For each major endpoint, provide detailed documentation with request/response examples."},
                {"name": "Error Handling", "instructions": "Document error codes and how to handle them."},
                {"name": "Code Examples", "instructions": "Provide practical code examples for using the API."},
            ],
            "QUALITY_AND_VALIDATION": [
                {"name": "Test Structure", "instructions": "Describe the test structure (unit, integration, e2e) and where tests are located."},
                {"name": "Running Tests", "instructions": "Document commands to run different types of tests."},
                {"name": "CI/CD Pipeline", "instructions": "THIS IS THE PRIMARY LOCATION for CI/CD documentation. Provide COMPREHENSIVE coverage: all workflows, triggers, jobs (with descriptions of what each does), required secrets, deployment environments, and how to debug failures."},
                {"name": "Code Quality Tools", "instructions": "Document linting, formatting, and static analysis tools used."},
                {"name": "Coverage Requirements", "instructions": "Document test coverage targets and how to generate reports."},
                {"name": "Branch Protection", "instructions": "Document branch protection rules and required checks before merging."},
            ],
            "USAGE_PATTERNS": [
                {"name": "Basic Usage", "instructions": "Provide the simplest working code example."},
                {"name": "Common Workflows", "instructions": "Document typical usage workflows with code examples."},
                {"name": "Integration Patterns", "instructions": "Show how to integrate with other systems."},
                {"name": "Advanced Usage", "instructions": "Document advanced features and patterns."},
                {"name": "Best Practices", "instructions": "List best practices and anti-patterns to avoid."},
            ],
            "DEVELOPER_WORKFLOWS": [
                {"name": "Setup", "instructions": "Document initial setup steps with exact commands."},
                {"name": "Development Workflow", "instructions": "Describe the development workflow (branch, code, test, PR)."},
                {"name": "Code Style", "instructions": "Document code style guidelines and how to enforce them."},
                {"name": "GitHub Configuration", "instructions": "THIS IS THE PRIMARY LOCATION for GitHub config. Document CODEOWNERS, issue/PR templates, dependabot, custom actions, and release process. Do NOT duplicate full CI/CD pipeline details (refer to QUALITY_AND_VALIDATION)."},
                {"name": "Common Tasks", "instructions": "Document common developer tasks with commands."},
            ],
            "GETTING_STARTED": [
                {"name": "Prerequisites", "instructions": "List all prerequisites with versions."},
                {"name": "Installation", "instructions": "Provide step-by-step installation instructions."},
                {"name": "Quick Start", "instructions": "Provide the minimal code/commands to verify the setup works."},
                {"name": "Next Steps", "instructions": "Guide users to other documentation and resources."},
            ],
        }

        return sections_map.get(doc_type, [
            {"name": "Overview", "instructions": "Provide a comprehensive overview of this topic."},
            {"name": "Details", "instructions": "Document the detailed information."},
            {"name": "Examples", "instructions": "Provide practical examples."},
        ])

    def _build_condensed_context(self, profile: RepositoryProfile, full_context: str) -> str:
        """Build a condensed version of context for chunked generation."""
        sections = [
            f"Repository: {profile.name}",
            f"Total files: {profile.total_files}",
            f"Languages: {profile.languages}",
            f"Tools: {profile.detected_tools}",
            f"Frameworks: {profile.detected_frameworks}",
        ]

        if profile.dependencies:
            deps = [d.name for d in profile.dependencies[:30]]
            sections.append(f"Dependencies: {', '.join(deps)}")

        if profile.env_variables:
            env_names = [e.name for e in profile.env_variables[:40]]
            sections.append(f"Environment variables: {', '.join(env_names)}")

        if profile.scripts:
            scripts = [f"{s.name}: {s.command}" for s in profile.scripts[:15]]
            sections.append(f"Scripts: {'; '.join(scripts)}")

        if profile.api_endpoints:
            apis = [f"{e.method} {e.path}" for e in profile.api_endpoints[:10]]
            sections.append(f"API endpoints: {', '.join(apis)}")

        if profile.ci_workflows:
            wfs = [f"{wf.name} ({wf.platform})" for wf in profile.ci_workflows]
            sections.append(f"CI/CD workflows: {', '.join(wfs)}")

        if profile.directory_summaries:
            dirs = [f"{d.path}: {d.description}" for d in profile.directory_summaries[:10]]
            sections.append(f"Key directories:\n  " + "\n  ".join(dirs))

        return "\n".join(sections)

    def _summarize_previous_sections(self, sections: list[str]) -> str:
        """Create a brief summary of previously generated sections."""
        if not sections:
            return ""
        # Just return section headers to provide context without overwhelming the prompt
        headers = []
        for section in sections:
            for line in section.split("\n"):
                if line.startswith("## "):
                    headers.append(line)
                    break
        return "Previous sections generated: " + ", ".join(h.replace("## ", "") for h in headers)

    def _call_llm(self, client, prompt: str, system: str) -> str:
        if self.provider == "openai":
            return self._call_openai(client, prompt, system)
        elif self.provider == "bedrock":
            return self._call_bedrock(client, prompt, system)
        raise RuntimeError(f"Unsupported provider: {self.provider}")

    def _call_openai(self, client, prompt: str, system: str) -> str:
        response = client.responses.create(
            model=self.model,
            instructions=system,
            input=prompt,
        )
        return getattr(response, "output_text", "").strip()

    def _call_bedrock(self, client, prompt: str, system: str) -> str:
        model_id = self.model

        # Handle model aliases
        if model_id in BEDROCK_MODELS:
            model_id = BEDROCK_MODELS[model_id]
        elif model_id == "gpt-4.1-mini":
            # Default fallback for OpenAI model - use Claude 3.7 Sonnet via inference profile
            model_id = BEDROCK_MODELS["claude-3.7-sonnet"]

        # Adjust max tokens based on model limits
        max_tokens = 4096  # Safe default for most models
        if "claude-3-opus" in model_id:
            max_tokens = 4096
        elif "claude-3-7-sonnet" in model_id:
            max_tokens = 8000  # Claude 3.7 supports higher limits
        elif "claude-3-5-haiku" in model_id:
            max_tokens = 4096
        elif "claude-3-sonnet" in model_id or "claude-3-haiku" in model_id:
            max_tokens = 4096
        elif "claude-sonnet-4" in model_id or "claude-opus-4" in model_id or "claude-haiku-4" in model_id:
            max_tokens = 8000  # Claude 4.x supports higher limits
        elif "titan" in model_id:
            max_tokens = 4096
        elif "llama" in model_id:
            max_tokens = 2048
        elif "mistral" in model_id:
            max_tokens = 4096

        try:
            response = client.converse(
                modelId=model_id,
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": max_tokens, "temperature": 0.3},
            )
        except client.exceptions.ValidationException as exc:
            raise RuntimeError(
                f"Bedrock model error: {exc}. "
                f"Available models: {', '.join(BEDROCK_MODELS.keys())}"
            ) from exc
        except client.exceptions.AccessDeniedException as exc:
            raise RuntimeError(
                f"Access denied to Bedrock model '{model_id}'. "
                "Ensure the model is enabled in your AWS account and IAM permissions are correct."
            ) from exc

        blocks = response.get("output", {}).get("message", {}).get("content", [])
        return "\n".join(b.get("text", "") for b in blocks if "text" in b).strip()

    def _build_client(self):
        if self.provider == "openai":
            return self._build_openai_client()
        if self.provider == "bedrock":
            return self._build_bedrock_client()
        raise RuntimeError(f"Unsupported AI provider: {self.provider}")

    def _build_openai_client(self):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed.") from exc
        if not self.is_configured():
            raise RuntimeError("OPENAI_API_KEY is not set.")
        return OpenAI()

    def _build_bedrock_client(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise RuntimeError("boto3 package not installed. Run: pip install boto3") from exc

        region = self.aws_region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if not region:
            raise RuntimeError(
                "AWS region not configured. Set AWS_REGION environment variable or use --aws-region flag."
            )

        self.aws_region = region
        boto_config = Config(
            read_timeout=3600,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        # AWS authentication priority:
        # 1. Explicit profile (includes SSO profiles configured via `aws configure sso`)
        # 2. IAM role assumption
        # 3. Default credential chain (SSO cached creds, env vars, instance profile, etc.)
        #
        # For AWS SSO, users should:
        #   1. Run: aws sso login --profile <profile-name>
        #   2. Use: --aws-profile <profile-name> or export AWS_PROFILE=<profile-name>
        #
        # boto3 automatically uses cached SSO credentials from ~/.aws/sso/cache/

        session = None
        profile = self.aws_profile or os.getenv("AWS_PROFILE")

        if profile:
            # This works for both regular profiles AND SSO profiles
            # SSO profiles work if user ran `aws sso login` first
            try:
                session = boto3.Session(profile_name=profile, region_name=region)
                # Validate the session has credentials
                credentials = session.get_credentials()
                if credentials is None:
                    raise RuntimeError(
                        f"No credentials found for profile '{profile}'. "
                        f"If using SSO, run: aws sso login --profile {profile}"
                    )
            except Exception as exc:
                if "SSO" in str(exc) or "sso" in str(exc).lower():
                    raise RuntimeError(
                        f"SSO session expired or not logged in. Run: aws sso login --profile {profile}"
                    ) from exc
                raise

        elif self.aws_role_arn or os.getenv("AWS_ROLE_ARN"):
            # Assume IAM role
            role_arn = self.aws_role_arn or os.getenv("AWS_ROLE_ARN")
            sts = boto3.client("sts", region_name=region)
            assumed = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName="runbook-ai-session",
                DurationSeconds=3600,
            )
            creds = assumed["Credentials"]
            session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
                region_name=region,
            )

        else:
            # Default credential chain - boto3 will automatically:
            # 1. Check environment variables (AWS_ACCESS_KEY_ID, etc.)
            # 2. Check ~/.aws/credentials and ~/.aws/config
            # 3. Check SSO cached credentials
            # 4. Check container credentials (ECS)
            # 5. Check instance metadata (EC2, Lambda)
            session = boto3.Session(region_name=region)

        return session.client("bedrock-runtime", config=boto_config)

    def _build_repo_context(self, profile: RepositoryProfile) -> str:
        sections = [
            f"# Repository: {profile.name}",
            f"Total files: {profile.total_files}",
            f"Languages: {profile.languages}",
            f"Categories: {profile.categories}",
            f"Tools: {profile.detected_tools}",
            f"Frameworks: {profile.detected_frameworks}",
        ]

        if profile.dependencies:
            deps = [f"{d.name}" + (f"=={d.version}" if d.version else "") for d in profile.dependencies[:40]]
            sections.append(f"Dependencies ({len(profile.dependencies)} total): {', '.join(deps)}")

        if profile.env_variables:
            env_list = [f"  {e.name}={e.default_value or '...'}" for e in profile.env_variables[:50]]
            sections.append(f"Environment variables ({len(profile.env_variables)} total):\n" + "\n".join(env_list))

        if profile.entry_points:
            entries = [f"  - {e.name}: {e.command or e.entry_type}" for e in profile.entry_points]
            sections.append(f"Entry points:\n" + "\n".join(entries))

        if profile.api_endpoints:
            apis = [f"  - {e.method} {e.path} ({e.source_file})" for e in profile.api_endpoints[:20]]
            sections.append(f"API endpoints ({len(profile.api_endpoints)} total):\n" + "\n".join(apis))

        if profile.scripts:
            scripts = [f"  - {s.name}: {s.command}" for s in profile.scripts[:25]]
            sections.append(f"Scripts/Commands ({len(profile.scripts)} total):\n" + "\n".join(scripts))

        # CI/CD Workflows
        if profile.ci_workflows:
            sections.append("\n# CI/CD WORKFLOWS")
            for wf in profile.ci_workflows:
                wf_lines = [
                    f"## {wf.name} ({wf.platform})",
                    f"   File: {wf.file_path}",
                ]
                if wf.triggers:
                    wf_lines.append(f"   Triggers: {', '.join(wf.triggers)}")
                if wf.jobs:
                    wf_lines.append(f"   Jobs: {', '.join(wf.jobs)}")
                if wf.environments:
                    wf_lines.append(f"   Environments: {', '.join(wf.environments)}")
                if wf.secrets_used:
                    wf_lines.append(f"   Secrets: {', '.join(wf.secrets_used)}")
                sections.append("\n".join(wf_lines))

        # GitHub Configuration
        if profile.github_config:
            gh = profile.github_config
            sections.append("\n# GITHUB REPOSITORY CONFIGURATION")
            gh_lines = []
            if gh.codeowners:
                gh_lines.append(f"CODEOWNERS: {len(gh.codeowners)} rules defined")
                for rule in gh.codeowners[:5]:
                    gh_lines.append(f"  {rule}")
                if len(gh.codeowners) > 5:
                    gh_lines.append(f"  ... and {len(gh.codeowners) - 5} more")
            if gh.dependabot_enabled:
                gh_lines.append(f"Dependabot: enabled for {', '.join(gh.dependabot_ecosystems)}")
            if gh.issue_templates:
                gh_lines.append(f"Issue Templates: {', '.join(gh.issue_templates)}")
            if gh.pr_template:
                gh_lines.append("PR Template: yes")
            if gh.custom_actions:
                gh_lines.append(f"Custom Actions: {', '.join(gh.custom_actions)}")
            if gh.protected_branches:
                gh_lines.append(f"Protected Branches (inferred): {', '.join(gh.protected_branches)}")
            if gh.release_drafter:
                gh_lines.append("Release Drafter: enabled")
            if gh.auto_release:
                gh_lines.append("Automated Releases: detected")
            if gh.funding:
                gh_lines.append(f"Funding: {', '.join(gh.funding)}")
            if gh_lines:
                sections.append("\n".join(gh_lines))

        # COMPLETE CODEBASE STRUCTURE - this is the key addition
        if profile.directory_summaries:
            sections.append("\n# COMPLETE CODEBASE STRUCTURE")
            sections.append("Below is a summary of EVERY directory in the repository:\n")

            for dir_sum in profile.directory_summaries:
                dir_section = [
                    f"## {dir_sum.path}/ ({dir_sum.file_count} files)",
                    f"   Purpose: {dir_sum.description}",
                    f"   Languages: {dir_sum.languages}",
                ]

                # Include symbols WITH descriptions (much more useful than just names)
                if dir_sum.symbols:
                    # Group by type
                    classes = [s for s in dir_sum.symbols if s.symbol_type == "class"]
                    functions = [s for s in dir_sum.symbols if s.symbol_type == "function"]
                    interfaces = [s for s in dir_sum.symbols if s.symbol_type == "interface"]

                    if classes:
                        dir_section.append("   Classes:")
                        for cls in classes[:15]:
                            desc = f" - {cls.docstring}" if cls.docstring else ""
                            sig = f"({cls.signature})" if cls.signature else ""
                            dir_section.append(f"     - {cls.name}{sig}{desc}")

                    if interfaces:
                        dir_section.append("   Interfaces/Types:")
                        for iface in interfaces[:10]:
                            desc = f" - {iface.docstring}" if iface.docstring else ""
                            dir_section.append(f"     - {iface.name}{desc}")

                    if functions:
                        dir_section.append("   Functions:")
                        for func in functions[:15]:
                            desc = f" - {func.docstring}" if func.docstring else ""
                            sig = func.signature if func.signature else "()"
                            dir_section.append(f"     - {func.name}{sig}{desc}")
                else:
                    # Fallback to just names if no symbols extracted
                    if dir_sum.all_classes:
                        dir_section.append(f"   Classes: {', '.join(dir_sum.all_classes[:20])}")
                    if dir_sum.all_functions:
                        dir_section.append(f"   Functions: {', '.join(dir_sum.all_functions[:20])}")

                if dir_sum.key_files:
                    dir_section.append(f"   Key files: {', '.join(dir_sum.key_files[:5])}")
                sections.append("\n".join(dir_section))

        # ALL FILE PATHS (compressed list)
        sections.append("\n# ALL FILES IN REPOSITORY")
        file_list = [str(f.path) for f in profile.file_insights]
        # Group by extension for compact representation
        by_ext: dict[str, list[str]] = {}
        for f in file_list:
            ext = Path(f).suffix or "no-ext"
            by_ext.setdefault(ext, []).append(f)

        for ext, files in sorted(by_ext.items(), key=lambda x: -len(x[1])):
            if len(files) <= 20:
                sections.append(f"{ext} files ({len(files)}): {', '.join(files)}")
            else:
                sections.append(f"{ext} files ({len(files)}): {', '.join(files[:15])}... and {len(files)-15} more")

        # Key file contents (reduced since we have full structure now)
        sections.append("\n# KEY FILE CONTENTS")
        for path, content in list(profile.important_file_contents.items())[:self.max_input_files]:
            truncated = content[:self.max_file_chars]
            sections.append(f"## {path}\n```\n{truncated}\n```")

        return "\n\n".join(sections)

    def _format_error(self, exc: Exception) -> str:
        msg = str(exc).lower()
        if "rate" in msg or "quota" in msg:
            return "Rate limit exceeded. Try again later."
        if "auth" in msg or "key" in msg:
            return "Authentication failed. Check API credentials."
        return f"API error: {exc}"
