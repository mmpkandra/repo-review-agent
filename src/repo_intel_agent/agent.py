from __future__ import annotations

from pathlib import Path

from .analyzer import RepositoryAnalyzer
from .docgen import AdaptiveDocGenerator
from .llm import OpenAIDocRefiner
from .models import GenerationResult


class RepoIntelligenceAgent:
    """High-level façade for repository profiling and adaptive doc generation."""

    def __init__(
        self,
        analyzer: RepositoryAnalyzer | None = None,
        doc_generator: AdaptiveDocGenerator | None = None,
        doc_refiner: OpenAIDocRefiner | None = None,
        compliance_scan: bool = False,
        compliance_level: str = "standard",
        generate_all_docs: bool = False,
        verbose: bool = True,
    ) -> None:
        self.analyzer = analyzer or RepositoryAnalyzer(
            compliance_scan=compliance_scan,
            compliance_level=compliance_level,
            generate_all_docs=generate_all_docs,
            verbose=verbose,
        )
        self.doc_generator = doc_generator or AdaptiveDocGenerator()
        self.doc_refiner = doc_refiner or OpenAIDocRefiner(verbose=verbose)
        self.generate_all_docs = generate_all_docs
        self.verbose = verbose

    def run(self, repo_path: str | Path, use_ai: bool = False) -> GenerationResult:
        root = Path(repo_path).resolve()
        profile = self.analyzer.analyze(root)
        warnings: list[str] = []

        if use_ai:
            # First, analyze semantics to enrich the profile
            try:
                self.doc_refiner.analyze_repository_semantics(profile)
            except RuntimeError as exc:
                warnings.append(f"Semantic analysis skipped: {exc}")

        # Generate docs (now with enriched profile if AI was used)
        artifacts = self.doc_generator.generate(profile)

        if use_ai:
            try:
                artifacts = self.doc_refiner.refine_artifacts(profile, artifacts)
            except RuntimeError as exc:
                warnings.append(str(exc))

        return GenerationResult(profile=profile, artifacts=artifacts, warnings=warnings)

    def write_docs(
        self,
        repo_path: str | Path,
        output_dir: str | Path,
        use_ai: bool = False,
    ) -> GenerationResult:
        result = self.run(repo_path, use_ai=use_ai)
        destination = Path(output_dir).resolve()
        destination.mkdir(parents=True, exist_ok=True)

        for artifact in result.artifacts:
            doc_path = destination / artifact.filename
            doc_path.write_text(artifact.body + "\n", encoding="utf-8")

        return result
