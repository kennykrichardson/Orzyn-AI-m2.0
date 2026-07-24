"""
============================================================
ORZYN AI m2.0
Repository Report Engine
============================================================

Purpose
-------
Transforms an Analysis into a deterministic report.

This module performs no AI inference.

It formats repository analysis into a structured report
consumable by the frontend, API, CLI, or exporters.

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.analyzer import (
    Analysis,
    analyze_repository,
)


# ============================================================
# Report Section
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class ReportSection:

    title: str

    data: Any


# ============================================================
# Repository Report
# ============================================================

@dataclass(
    slots=True,
)
class RepositoryReport:

    analysis: Analysis

    sections: list[ReportSection] = field(
        default_factory=list,
    )

    generated: bool = False

# ============================================================
# Repository Overview
# ============================================================

def repository_overview(
    analysis: Analysis,
) -> ReportSection:

    return ReportSection(

        title="Repository Overview",

        data={

            "owner": analysis.summary.owner,

            "repository": analysis.summary.repository,

            "framework": analysis.summary.framework,

            "language": analysis.summary.language,

            "stars": analysis.summary.stars,

            "forks": analysis.summary.forks,

            "supported_files": (

                analysis.summary.supported_files

            ),

            "selected_files": (

                analysis.summary.selected_files

            ),

        },

    )


# ============================================================
# Overall Health
# ============================================================

def overall_health(
    analysis: Analysis,
) -> ReportSection:

    report = analysis.health_report

    return ReportSection(

        title="Overall Health",

        data={

            "overall_score": report.overall_score,

            "confidence": report.confidence,

            "repository_type": report.repository_type.value,

            "strengths": report.strengths,

            "weaknesses": report.weaknesses,

            "recommendations": report.recommendations,

        },

    )


# ============================================================
# Technology Stack
# ============================================================

def technology_stack(
    analysis: Analysis,
) -> ReportSection:

    return ReportSection(

        title="Technology Stack",

        data={

            "framework": (

                analysis.summary.framework

            ),

            "primary_language": (

                analysis.summary.language

            ),

            "languages": (

                analysis.codebase.statistics
                .language_distribution

            ),

        },

    )


# ============================================================
# Metrics
# ============================================================

def repository_metrics(
    analysis: Analysis,
) -> ReportSection:

    statistics = analysis.codebase.statistics

    return ReportSection(

        title="Repository Metrics",

        data={

            "total_files": (

                statistics.total_files

            ),

            "supported_files": (

                statistics.supported_files

            ),

            "ignored_files": (

                statistics.ignored_files

            ),

            "execution_time_ms": (

                analysis.execution_time_ms

            ),

        },

    )

# ============================================================
# Analyzer Results
# ============================================================

def analyzer_results(
    analysis: Analysis,
) -> ReportSection:

    analyzers: dict[
        str,
        Any,
    ] = {}

    for result in analysis.analyzers:

        payload = result.payload

        if hasattr(
            payload,
            "__dict__",
        ):

            value = vars(
                payload,
            )

        else:

            value = payload

        analyzers[
            result.name
        ] = {

            "duration_ms": result.duration_ms,

            "result": value,

        }

    return ReportSection(

        title="Analyzer Results",

        data=analyzers,

    )


# ============================================================
# Executive Summary
# ============================================================

def executive_summary(
    analysis: Analysis,
) -> ReportSection:

    score = analysis.health_report.overall_score

    if score >= 90:

        verdict = (
            "Excellent repository quality."
        )

    elif score >= 80:

        verdict = (
            "Healthy repository with minor improvements."
        )

    elif score >= 70:

        verdict = (
            "Good repository with noticeable technical debt."
        )

    elif score >= 60:

        verdict = (
            "Repository requires attention."
        )

    else:

        verdict = (
            "Repository requires significant improvements."
        )

    return ReportSection(

        title="Executive Summary",

        data={

            "overall_score": (

                analysis.overall_score

            ),

            "confidence": (

                analysis.health_report.confidence

            ),

            "verdict": verdict,

        },

    )


# ============================================================
# Report Builder
# ============================================================

def build_report(
    analysis: Analysis,
) -> RepositoryReport:

    sections = [

        repository_overview(
            analysis,
        ),

        overall_health(
            analysis,
        ),

        technology_stack(
            analysis,
        ),

        repository_metrics(
            analysis,
        ),

        analyzer_results(
            analysis,
        ),

        executive_summary(
            analysis,
        ),

    ]

    return RepositoryReport(

        analysis=analysis,

        sections=sections,

        generated=True,

    )

# ============================================================
# Public API
# ============================================================

def generate_report(
    analysis: Analysis,
) -> RepositoryReport:

    """
    Build a report from an existing
    Analysis instance.
    """

    return build_report(
        analysis,
    )


def analyze_and_report(
) -> RepositoryReport:

    """
    Execute the complete deterministic
    analysis pipeline and return the
    finished report.
    """

    analysis = analyze_repository()

    return build_report(
        analysis,
    )


# ============================================================
# Utility Functions
# ============================================================

def report_as_dict(
    report: RepositoryReport,
) -> dict[str, Any]:

    return {

        section.title: section.data

        for section in report.sections

    }


def section(
    report: RepositoryReport,
    title: str,
) -> ReportSection:

    for item in report.sections:

        if item.title == title:

            return item

    raise KeyError(
        f"Unknown report section: {title}"
    )


def section_titles(
    report: RepositoryReport,
) -> tuple[str, ...]:

    return tuple(

        item.title

        for item in report.sections

    )


def total_sections(
    report: RepositoryReport,
) -> int:

    return len(
        report.sections,
    )


# ============================================================
# Exports
# ============================================================

__all__ = [

    "ReportSection",

    "RepositoryReport",

    "repository_overview",

    "overall_health",

    "technology_stack",

    "repository_metrics",

    "analyzer_results",

    "executive_summary",

    "build_report",

    "generate_report",

    "analyze_and_report",

    "report_as_dict",

    "section",

    "section_titles",

    "total_sections",

]