"""
============================================================
ORZYN AI m2.0
Source Code Intelligence Runner
============================================================

Purpose
-------
Run the complete deterministic repository analysis pipeline
and generate an AI-powered engineering review.

Responsibilities
----------------
• Validate environment
• Configure target repository
• Execute deterministic analysis
• Generate LLM engineering review
• Display summary
• Exit with appropriate status
"""

from __future__ import annotations

import sys

from backend.code_ai import (
    CodeReview,
    review_repository,
)

from backend.orzyn import (
    validate_environment,
)

from backend.orzyn import (
    get_active_repository,
    set_active_repository,
)


# ============================================================
# Output
# ============================================================

def print_summary(
    review: CodeReview,
) -> None:

    report = review.report

    analysis = report.analysis

    codebase = analysis.codebase

    metadata = codebase.metadata

    print("\n" + "=" * 72)
    print("ORZYN AI m2.0")
    print("SOURCE CODE INTELLIGENCE")
    print("=" * 72)

    print(f"Repository      : {metadata.name}")
    print(f"Owner           : {get_active_repository().owner}")

    print(
        f"Repository Type : "
        f"{codebase.repository_type.value}"
    )

    print(
        f"Framework       : "
        f"{codebase.framework}"
    )

    print(
        f"Language        : "
        f"{codebase.primary_language}"
    )

    print(
        f"Overall Score   : "
        f"{analysis.overall_score:.2f}"
    )

    print(
        f"Health Grade    : "
        f"{analysis.health_report.confidence}"
    )

    print()

    print(
        f"Files           : "
        f"{len(codebase.files)}"
    )

    print(
        f"Analyzers       : "
        f"{len(analysis.analyzers)}"
    )

    print(
        f"Execution Time  : "
        f"{analysis.execution_time_ms:.2f} ms"
    )

    print()

    print("-" * 72)
    print("AI ENGINEERING REVIEW")
    print("-" * 72)
    print()

    print(
        review.response.response,
    )

    print()
    print("=" * 72)


# ============================================================
# Runner
# ============================================================

def run(
    repository: str | None = None,
) -> CodeReview:

    validate_environment()

    if repository:

        set_active_repository(
            repository,
        )

    return review_repository()


# ============================================================
# Main
# ============================================================

def main() -> int:

    try:

        repository = (

            sys.argv[1]

            if len(sys.argv) > 1

            else None

        )

        review = run(
            repository,
        )

        print_summary(
            review,
        )

        return 0

    except KeyboardInterrupt:

        print("\nOperation cancelled.")

        return 130

if __name__ == "__main__":

    raise SystemExit(
        main()
    )