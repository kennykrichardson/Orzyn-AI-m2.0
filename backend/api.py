"""
============================================================
ORZYN AI m2.0
Public Backend API
============================================================

Purpose
-------
Expose the complete deterministic Orzyn pipeline.

This module is the only entry point external consumers
should use.

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from backend.analyzer import (
    Analysis,
    analyze_codebase,
    analyze_repository,
)

from backend.codebase import (
    Codebase,
    fetch_codebase,
)

from backend.report import (
    RepositoryReport,
    analyze_and_report,
    generate_report,
)

# ============================================================
# Codebase API
# ============================================================

def codebase(
) -> Codebase:

    """
    Build and return the deterministic
    repository representation.
    """

    return fetch_codebase()


# ============================================================
# Analysis API
# ============================================================

def analysis(
) -> Analysis:

    """
    Analyze the active repository.
    """

    return analyze_repository()


def analyze(
    codebase: Codebase,
) -> Analysis:

    """
    Analyze an existing Codebase.
    """

    return analyze_codebase(
        codebase,
    )


# ============================================================
# Report API
# ============================================================

def report(
) -> RepositoryReport:

    """
    Execute the complete analysis
    pipeline and generate a report.
    """

    return analyze_and_report()


def build_report(
    analysis: Analysis,
) -> RepositoryReport:

    """
    Build a report from an existing
    Analysis.
    """

    return generate_report(
        analysis,
    )

# ============================================================
# Serialization
# ============================================================

def codebase_dict(
    codebase: Codebase,
) -> dict[str, Any]:

    return asdict(
        codebase,
    )


def analysis_dict(
    analysis: Analysis,
) -> dict[str, Any]:

    return asdict(
        analysis,
    )


def report_dict(
    report: RepositoryReport,
) -> dict[str, Any]:

    return asdict(
        report,
    )


# ============================================================
# Convenience
# ============================================================

def full_pipeline(
) -> tuple[
    Codebase,
    Analysis,
    RepositoryReport,
]:

    repository = fetch_codebase()

    repository_analysis = analyze_codebase(
        repository,
    )

    repository_report = generate_report(
        repository_analysis,
    )

    return (

        repository,

        repository_analysis,

        repository_report,

    )

# ============================================================
# Version
# ============================================================

API_VERSION = "2.0.0"


# ============================================================
# Exports
# ============================================================

__all__ = [

    "API_VERSION",

    "codebase",

    "analysis",

    "analyze",

    "report",

    "build_report",

    "codebase_dict",

    "analysis_dict",

    "report_dict",

    "full_pipeline",

]