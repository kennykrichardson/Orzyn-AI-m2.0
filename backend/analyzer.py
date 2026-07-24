"""
============================================================
ORZYN AI m2.0
Repository Analysis Orchestrator
============================================================

Purpose
-------
Coordinates every deterministic analyzer inside Orzyn.

This module performs no repository parsing and no AI inference.

It receives a Codebase object, executes every analysis engine,
aggregates their results, computes the overall repository
assessment, and produces a single immutable Analysis object.

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from time import perf_counter
from typing import Any

from backend.codebase import (
    Codebase,
    RepositoryMetadata,
    fetch_codebase,
)
from backend.health_score import (
    HealthReport,
    build_health_report,
)


# ============================================================
# Analyzer Result
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class AnalyzerResult:

    name: str

    duration_ms: float

    payload: Any


# ============================================================
# Repository Summary
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class RepositorySummary:

    owner: str

    repository: str

    framework: str

    language: str | None

    stars: int

    forks: int

    supported_files: int

    selected_files: int


# ============================================================
# Analysis
# ============================================================

@dataclass(
    slots=True,
)
class Analysis:

    metadata: RepositoryMetadata

    summary: RepositorySummary

    codebase: Codebase

    health_report: HealthReport

    analyzers: list[AnalyzerResult] = field(
        default_factory=list,
    )

    overall_score: float = 0.0

    execution_time_ms: float = 0.0


# ============================================================
# Analyzer Base
# ============================================================

class Analyzer:

    name = "Analyzer"

    def analyze(
        self,
        codebase: Codebase,
    ) -> Any:

        raise NotImplementedError

# ============================================================
# Health Score Analyzer
# ============================================================

class HealthScoreAnalyzer(
    Analyzer,
):

    name = "Health Score"

    def analyze(
        self,
        codebase: Codebase,
    ) -> HealthReport:

        return build_health_report(
            repository=codebase.repository,

            commits=codebase.commits,

            pull_requests=codebase.pull_requests,

            issues=codebase.issues,

            developers=codebase.developers,

        )


# ============================================================
# Analyzer Execution
# ============================================================

def execute_analyzer(
    analyzer: Analyzer,
    codebase: Codebase,
) -> AnalyzerResult:

    start = perf_counter()

    payload = analyzer.analyze(
        codebase,
    )

    elapsed = (

        perf_counter()

        - start

    ) * 1000

    return AnalyzerResult(

        name=analyzer.name,

        duration_ms=round(

            elapsed,

            3,

        ),

        payload=payload,

    )


# ============================================================
# Registered Analyzers
# ============================================================

REGISTERED_ANALYZERS: list[
    Analyzer
] = [

    HealthScoreAnalyzer(),

]


# ============================================================
# Repository Summary Builder
# ============================================================

def build_summary(
    codebase: Codebase,
) -> RepositorySummary:

    return RepositorySummary(

        owner=codebase.metadata.owner,

        repository=codebase.metadata.name,

        framework=codebase.framework,

        language=codebase.primary_language,

        stars=codebase.metadata.stars,

        forks=codebase.metadata.forks,

        supported_files=(

            codebase.statistics.supported_files

        ),

        selected_files=len(
            codebase.files,
        ),

    )


# ============================================================
# Overall Score
# ============================================================

def calculate_overall_score(
    results: list[
        AnalyzerResult
    ],
) -> float:

    scores: list[
        float
    ] = []

    for result in results:

        payload = result.payload

        score = getattr(

            payload,

            "overall_score",

            None,

        )

        if isinstance(

            score,

            (int, float),

        ):

            scores.append(
                float(score)
            )

    if not scores:

        return 0.0

    return round(

        mean(
            scores,
        ),

        2,

    )

# ============================================================
# Analysis Builder
# ============================================================

def build_analysis(
    codebase: Codebase,
) -> Analysis:

    start = perf_counter()

    results: list[
        AnalyzerResult
    ] = []

    health_report: HealthReport | None = None

    for analyzer in REGISTERED_ANALYZERS:

        result = execute_analyzer(

            analyzer,

            codebase,

        )

        results.append(
            result,
        )

        if isinstance(

            result.payload,

            HealthReport,

        ):

            health_report = result.payload

    if health_report is None:

        raise RuntimeError(

            "Health Score analyzer was not executed."

        )

    elapsed = (

        perf_counter()

        - start

    ) * 1000

    return Analysis(

        metadata=codebase.metadata,

        summary=build_summary(
            codebase,
        ),

        codebase=codebase,

        health_report=health_report,

        analyzers=results,

        overall_score=calculate_overall_score(
            results,
        ),

        execution_time_ms=round(

            elapsed,

            3,

        ),

    )


# ============================================================
# Public API
# ============================================================

def analyze_codebase(
    codebase: Codebase,
) -> Analysis:

    """
    Execute every registered analyzer against
    an existing Codebase instance.
    """

    return build_analysis(
        codebase,
    )


def analyze_repository(
) -> Analysis:

    """
    Build the repository Codebase and execute
    every registered analyzer.
    """

    codebase = fetch_codebase()

    return build_analysis(
        codebase,
    )


# ============================================================
# Utility Functions
# ============================================================

def analyzer_results(
    analysis: Analysis,
) -> dict[str, Any]:

    return {

        result.name: result.payload

        for result in analysis.analyzers

    }


def analyzer_timings(
    analysis: Analysis,
) -> dict[str, float]:

    return {

        result.name: result.duration_ms

        for result in analysis.analyzers

    }


def total_analyzers(
    analysis: Analysis,
) -> int:

    return len(
        analysis.analyzers,
    )


# ============================================================
# Exports
# ============================================================

__all__ = [

    "Analyzer",

    "AnalyzerResult",

    "RepositorySummary",

    "Analysis",

    "HealthScoreAnalyzer",

    "REGISTERED_ANALYZERS",

    "execute_analyzer",

    "build_summary",

    "calculate_overall_score",

    "build_analysis",

    "analyze_codebase",

    "analyze_repository",

    "analyzer_results",

    "analyzer_timings",

    "total_analyzers",

]