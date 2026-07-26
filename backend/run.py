"""
============================================================
ORZYN AI m2.0
Backend Integration Runner
============================================================

Purpose
-------
Run the complete Orzyn AI backend pipeline.

Responsibilities
----------------
• Validate environment
• Configure target repository
• Execute repository analysis
• Display engineering summary
• Exit with appropriate status
"""

from __future__ import annotations

import sys

from backend.ai_model import (
    AIAnalysis,
    analyze_repository,
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
    analysis: AIAnalysis,
) -> None:

    print("\n" + "=" * 72)
    print("ORZYN AI m2.0")
    print("=" * 72)

    print(f"Repository      : {analysis.repository.name}")
    print(f"Owner           : {get_active_repository().owner}")

    print(
        f"Repository Type : "
        f"{analysis.health.repository_type.value}"
    )

    print(
        f"Health Score    : "
        f"{analysis.health.overall_score:.2f}/100"
    )

    print(
        f"Confidence      : "
        f"{analysis.health.confidence:.2f}%"
    )

    print()

    print(
        f"Commits         : {len(analysis.commits)}"
    )

    print(
        f"Pull Requests   : {len(analysis.pull_requests)}"
    )

    print(
        f"Issues          : {len(analysis.issues)}"
    )

    print(
        f"Developers      : {len(analysis.developers)}"
    )

    print()

    print("-" * 72)
    print("AI ENGINEERING REPORT")
    print("-" * 72)
    print()

    print(analysis.response.response)

    print()
    print("=" * 72)


# ============================================================
# Runner
# ============================================================

def run(
    repository: str | None = None,
) -> AIAnalysis:

    validate_environment()

    if repository:

        set_active_repository(
            repository,
        )

    analysis = analyze_repository()

    return analysis


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

        analysis = run(
            repository,
        )

        print_summary(
            analysis,
        )

        return 0

    except KeyboardInterrupt:

        print("\nOperation cancelled.")

        return 130

    except Exception as exc:

        print()

        print("=" * 72)

        print("ORZYN ERROR")

        print("=" * 72)

        print(exc)

        print("=" * 72)

        return 1


if __name__ == "__main__":

    raise SystemExit(
        main()
    )