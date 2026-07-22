"""
============================================================
ORZYN AI m3.0
Repository Health Engine
============================================================

Purpose
-------
Produce deterministic, explainable engineering health scores.

Design Principles
-----------------
• Deterministic
• Explainable
• Context-aware
• Repository-type aware
• AI-independent
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from backend.repository import RepositoryProfile
from backend.commits import CommitProfile
from backend.pull_requests import PullRequestProfile
from backend.issues import IssueProfile
from backend.developer import DeveloperProfile


# ============================================================
# Repository Types
# ============================================================

class RepositoryType(Enum):

    PERSONAL = "Personal"

    STUDENT = "Student"

    OPEN_SOURCE = "Open Source"

    ENTERPRISE = "Enterprise"

    RESEARCH = "Research"

    UNKNOWN = "Unknown"


# ============================================================
# Metric Status
# ============================================================

class MetricStatus(Enum):

    AVAILABLE = "Available"

    NOT_APPLICABLE = "Not Applicable"

    MISSING = "Missing"


# ============================================================
# Metric
# ============================================================

@dataclass(slots=True)
class Metric:

    name: str

    earned: float

    possible: float

    explanation: str

    status: MetricStatus

    evidence: list[str]

    recommendation: str | None = None

    @property
    def score(self) -> float:

        if self.possible == 0:
            return 100.0

        return (self.earned / self.possible) * 100


# ============================================================
# Category
# ============================================================

@dataclass(slots=True)
class Category:

    name: str

    weight: float

    explanation: str

    metrics: list[Metric]

    @property
    def earned(self):

        return sum(

            metric.earned

            for metric in self.metrics

            if metric.status is MetricStatus.AVAILABLE

        )

    @property
    def possible(self):

        return sum(

            metric.possible

            for metric in self.metrics

            if metric.status is MetricStatus.AVAILABLE

        )

    @property
    def score(self):

        if self.possible == 0:
            return 100.0

        return (

            self.earned

            /

            self.possible

        ) * 100


# ============================================================
# Health Report
# ============================================================

@dataclass(slots=True)
class HealthReport:

    repository: RepositoryProfile

    repository_type: RepositoryType

    overall_score: float

    confidence: float

    categories: list[Category]

    strengths: list[str]

    weaknesses: list[str]

    recommendations: list[str]


# ============================================================
# Repository Rubrics
# ============================================================

RUBRICS = {

    RepositoryType.PERSONAL: {

        "Repository": 35,

        "Development": 40,

        "Architecture": 15,

        "Community": 5,

        "Collaboration": 0,

        "Issues": 5,

    },

    RepositoryType.STUDENT: {

        "Repository": 30,

        "Development": 40,

        "Architecture": 15,

        "Community": 5,

        "Collaboration": 5,

        "Issues": 5,

    },

    RepositoryType.OPEN_SOURCE: {

        "Repository": 20,

        "Development": 25,

        "Architecture": 15,

        "Community": 15,

        "Collaboration": 15,

        "Issues": 10,

    },

    RepositoryType.ENTERPRISE: {

        "Repository": 20,

        "Development": 20,

        "Architecture": 20,

        "Community": 10,

        "Collaboration": 20,

        "Issues": 10,

    },

    RepositoryType.RESEARCH: {

        "Repository": 30,

        "Development": 35,

        "Architecture": 20,

        "Community": 5,

        "Collaboration": 5,

        "Issues": 5,

    },

}

# ============================================================
# Helpers
# ============================================================

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def percentage(
    earned: float,
    possible: float,
) -> float:

    if possible <= 0:
        return 100.0

    return (

        earned

        /

        possible

    ) * 100


def create_metric(
    name: str,
    earned: float,
    possible: float,
    explanation: str,
    status: MetricStatus = MetricStatus.AVAILABLE,
    evidence: list[str] | None = None,
    recommendation: str | None = None,
) -> Metric:

    return Metric(

        name=name,

        earned=earned,

        possible=possible,

        explanation=explanation,

        status=status,

        evidence=evidence or [],

        recommendation=recommendation,

    )


# ============================================================
# Repository Classification
# ============================================================

PERSONAL_KEYWORDS = {

    "portfolio",
    "resume",
    "website",
    "personal",
    "cv",

}

STUDENT_KEYWORDS = {

    "assignment",
    "college",
    "lab",
    "project",
    "semester",

}


def classify_repository(
    repository: RepositoryProfile,
    commits: list[CommitProfile],
    developers: list[DeveloperProfile],
) -> RepositoryType:

    name = repository.name.lower()

    description = (

        repository.description or ""

    ).lower()

    text = f"{name} {description}"

    contributors = len(developers)

    commit_count = len(commits)

    stars = repository.stars

    forks = repository.forks

    # --------------------------------------------------------
    # Personal Portfolio
    # --------------------------------------------------------

    if any(

        keyword in text

        for keyword in PERSONAL_KEYWORDS

    ):

        return RepositoryType.PERSONAL

    # --------------------------------------------------------
    # Student Project
    # --------------------------------------------------------

    if any(

        keyword in text

        for keyword in STUDENT_KEYWORDS

    ):

        return RepositoryType.STUDENT

    # --------------------------------------------------------
    # Large Open Source
    # --------------------------------------------------------

    if (

        contributors >= 10

        or

        stars >= 100

        or

        forks >= 25

    ):

        return RepositoryType.OPEN_SOURCE

    # --------------------------------------------------------
    # Enterprise
    # --------------------------------------------------------

    if (

        contributors >= 50

        and

        commit_count >= 1000

    ):

        return RepositoryType.ENTERPRISE

    # --------------------------------------------------------
    # Default Personal

    # One maintainer should NEVER be penalized.

    # --------------------------------------------------------

    if contributors <= 2:

        return RepositoryType.PERSONAL

    return RepositoryType.RESEARCH


# ============================================================
# Category Factory
# ============================================================

def create_category(
    repository_type: RepositoryType,
    name: str,
    metrics: list[Metric],
    explanation: str,
) -> Category:

    return Category(

        name=name,

        weight=RUBRICS[repository_type][name],

        explanation=explanation,

        metrics=metrics,

    )


# ============================================================
# Confidence
# ============================================================

def calculate_confidence(
    categories: list[Category],
) -> float:

    available = 0

    total = 0

    for category in categories:

        for metric in category.metrics:

            if metric.status is MetricStatus.NOT_APPLICABLE:

                continue

            total += 1

            if metric.status is MetricStatus.AVAILABLE:

                available += 1

    if total == 0:

        return 100.0

    return percentage(

        available,

        total,

    )

# ============================================================
# Repository Metrics
# ============================================================

def build_repository_metrics(
    repository: RepositoryProfile,
    repository_type: RepositoryType,
) -> list[Metric]:

    metrics: list[Metric] = []

    # --------------------------------------------------------

    metrics.append(

        create_metric(

            name="Repository Description",

            earned=10 if repository.description else 0,

            possible=10,

            explanation=(
                "Repository contains a description."
                if repository.description
                else "Repository description is missing."
            ),

            recommendation=(
                None
                if repository.description
                else "Add a clear repository description."
            ),

        )

    )

    # --------------------------------------------------------

    metrics.append(

        create_metric(

            name="Default Branch",

            earned=5 if repository.default_branch else 0,

            possible=5,

            explanation=(
                "Default branch configured."
                if repository.default_branch
                else "No default branch detected."
            ),

            recommendation=(
                None
                if repository.default_branch
                else "Configure a default branch."
            ),

        )

    )

    # --------------------------------------------------------

    metrics.append(

        create_metric(

            name="Visibility",

            earned=5,

            possible=5,

            explanation=f"Repository is {repository.visibility}.",

        )

    )

    # --------------------------------------------------------
    # Stars
    # --------------------------------------------------------

    if repository_type is RepositoryType.OPEN_SOURCE:

        metrics.append(

            create_metric(

                name="Stars",

                earned=min(repository.stars, 20),

                possible=20,

                explanation=f"{repository.stars} GitHub stars.",

                recommendation=(
                    None
                    if repository.stars > 0
                    else "Increase community visibility."
                ),

            )

        )

    else:

        metrics.append(

            create_metric(

                name="Stars",

                earned=0,

                possible=0,

                explanation="Stars are not used when evaluating personal repositories.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        )

    # --------------------------------------------------------
    # Forks
    # --------------------------------------------------------

    if repository_type is RepositoryType.OPEN_SOURCE:

        metrics.append(

            create_metric(

                name="Forks",

                earned=min(repository.forks, 10),

                possible=10,

                explanation=f"{repository.forks} repository forks.",

            )

        )

    else:

        metrics.append(

            create_metric(

                name="Forks",

                earned=0,

                possible=0,

                explanation="Fork count is not relevant for this repository type.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        )

    return metrics


# ============================================================
# Development Metrics
# ============================================================

def build_development_metrics(
    commits: list[CommitProfile],
) -> list[Metric]:

    if not commits:

        return [

            create_metric(

                "Commit History",

                0,

                25,

                "No commit history available.",

                status=MetricStatus.MISSING,

                recommendation="Commit project changes regularly.",

            )

        ]

    commit_count = len(commits)

    average_changes = (

        sum(

            commit.additions + commit.deletions

            for commit in commits

        )

        /

        commit_count

    )

    largest_commit = max(

        commits,

        key=lambda commit:

        commit.additions +

        commit.deletions,

    )

    metrics: list[Metric] = []

    # --------------------------------------------------------

    metrics.append(

        create_metric(

            "Commit Frequency",

            min(commit_count, 20),

            20,

            f"{commit_count} commits analysed.",

        )

    )

    # --------------------------------------------------------

    size_score = 20

    recommendation = None

    if average_changes > 800:

        size_score = 8

        recommendation = (

            "Reduce commit size into smaller logical commits."

        )

    elif average_changes > 500:

        size_score = 14

        recommendation = (

            "Prefer smaller commits where practical."

        )

    metrics.append(

        create_metric(

            "Commit Granularity",

            size_score,

            20,

            f"Average commit changed {average_changes:.0f} lines.",

            recommendation=recommendation,

        )

    )

    # --------------------------------------------------------

    metrics.append(

        create_metric(

            "Largest Commit",

            5 if (

                largest_commit.additions +

                largest_commit.deletions

            ) < 2500 else 2,

            5,

            f"Largest commit: {largest_commit.message}",

        )

    )

    return metrics


# ============================================================
# Collaboration Metrics
# ============================================================

def build_collaboration_metrics(
    repository_type: RepositoryType,
    developers: list[DeveloperProfile],
    pull_requests: list[PullRequestProfile],
) -> list[Metric]:

    # Personal repositories

    if repository_type is RepositoryType.PERSONAL:

        return [

            create_metric(

                "Collaboration",

                0,

                0,

                "Single-maintainer workflow detected.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        ]

    total = len(pull_requests)

    merged = sum(

        pr.merged

        for pr in pull_requests

    )

    merge_rate = (

        merged / total

        if total

        else 0

    )

    return [

        create_metric(

            "Merge Rate",

            merge_rate * 20,

            20,

            f"{merged}/{total} pull requests merged.",

        )

    ]


# ============================================================
# Issue Metrics
# ============================================================

def build_issue_metrics(
    repository_type: RepositoryType,
    issues: list[IssueProfile],
) -> list[Metric]:

    if repository_type is RepositoryType.PERSONAL:

        return [

            create_metric(

                "Issue Tracking",

                0,

                0,

                "Issue tracking is optional for personal repositories.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        ]

    if not issues:

        return [

            create_metric(

                "Issue Tracking",

                0,

                10,

                "No issues available.",

                recommendation="Use GitHub Issues to track work.",

            )

        ]

    closed = sum(

        issue.closed

        for issue in issues

    )

    total = len(issues)

    return [

        create_metric(

            "Issue Resolution",

            (closed / total) * 20,

            20,

            f"{closed}/{total} issues closed.",

        )

    ]


# ============================================================
# Community Metrics
# ============================================================

def build_community_metrics(
    repository_type: RepositoryType,
    developers: list[DeveloperProfile],
) -> list[Metric]:

    if repository_type is RepositoryType.PERSONAL:

        return [

            create_metric(

                "Community",

                0,

                0,

                "Community metrics are not evaluated for personal repositories.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        ]

    contributors = len(developers)

    return [

        create_metric(

            "Contributors",

            min(contributors * 2, 20),

            20,

            f"{contributors} contributors.",

        )

    ]

# ============================================================
# Strength Builder
# ============================================================

def build_strengths(
    categories: list[Category],
) -> list[str]:

    strengths: list[str] = []

    for category in categories:

        for metric in category.metrics:

            if (

                metric.status is MetricStatus.AVAILABLE

                and

                metric.score >= 90

            ):

                strengths.append(metric.explanation)

    if not strengths:

        strengths.append(

            "Repository contains measurable engineering practices."

        )

    return strengths


# ============================================================
# Weakness Builder
# ============================================================

def build_weaknesses(
    categories: list[Category],
) -> list[str]:

    weaknesses: list[str] = []

    for category in categories:

        for metric in category.metrics:

            if (

                metric.status is MetricStatus.AVAILABLE

                and

                metric.score < 50

            ):

                weaknesses.append(

                    metric.explanation

                )

    return weaknesses


# ============================================================
# Recommendation Builder
# ============================================================

def build_recommendations(
    categories: list[Category],
) -> list[str]:

    recommendations: list[str] = []

    for category in categories:

        for metric in category.metrics:

            if (

                metric.recommendation

                and

                metric.recommendation

                not in recommendations

            ):

                recommendations.append(

                    metric.recommendation

                )

    if not recommendations:

        recommendations.append(

            "Continue following current engineering practices."

        )

    return recommendations


# ============================================================
# Health Report Builder
# ============================================================

def build_health_report(
    repository: RepositoryProfile,
    commits: list[CommitProfile],
    pull_requests: list[PullRequestProfile],
    issues: list[IssueProfile],
    developers: list[DeveloperProfile],
) -> HealthReport:

    repository_type = classify_repository(

        repository,

        commits,

        developers,

    )

    categories = [

        create_category(

            repository_type,

            "Repository",

            build_repository_metrics(

                repository,

                repository_type,

            ),

            "Repository metadata and configuration.",

        ),

        create_category(

            repository_type,

            "Development",

            build_development_metrics(

                commits,

            ),

            "Commit history and development practices.",

        ),

        create_category(

            repository_type,

            "Architecture",

            [

                create_metric(

                    "Architecture",

                    100,

                    100,

                    "Architecture analysis is reserved for source-code inspection.",

                    status=MetricStatus.NOT_APPLICABLE,

                )

            ],

            "Architecture metrics.",

        ),

        create_category(

            repository_type,

            "Collaboration",

            build_collaboration_metrics(

                repository_type,

                developers,

                pull_requests,

            ),

            "Collaboration practices.",

        ),

        create_category(

            repository_type,

            "Issues",

            build_issue_metrics(

                repository_type,

                issues,

            ),

            "Issue management.",

        ),

        create_category(

            repository_type,

            "Community",

            build_community_metrics(

                repository_type,

                developers,

            ),

            "Community engagement.",

        ),

    ]

    overall = 0.0

    total_weight = 0.0

    for category in categories:

        if category.weight == 0:

            continue

        overall += (

            category.score

            *

            category.weight

        )

        total_weight += category.weight

    overall = (

        overall / total_weight

        if total_weight

        else 100

    )

    overall = clamp(overall)

    confidence = calculate_confidence(

        categories,

    )

    strengths = build_strengths(

        categories,

    )

    weaknesses = build_weaknesses(

        categories,

    )

    recommendations = build_recommendations(

        categories,

    )

    return HealthReport(

        repository=repository,

        repository_type=repository_type,

        overall_score=overall,

        confidence=confidence,

        categories=categories,

        strengths=strengths,

        weaknesses=weaknesses,

        recommendations=recommendations,

    )


# ============================================================
# DataFrame
# ============================================================

def health_dataframe(
    report: HealthReport,
) -> pd.DataFrame:

    rows: list[dict[str, object]] = []

    for category in report.categories:

        for metric in category.metrics:

            rows.append({

                "Category": category.name,

                "Metric": metric.name,

                "Score": round(metric.score, 2),

                "Status": metric.status.value,

                "Explanation": metric.explanation,

                "Recommendation": metric.recommendation or "",

                "Evidence": ", ".join(metric.evidence),

            })

    return pd.DataFrame(rows)


# ============================================================
# Statistics
# ============================================================

def health_statistics(
    report: HealthReport,
) -> dict[str, object]:

    return {

        "repository": report.repository.name,

        "repository_type": report.repository_type.value,

        "overall_score": round(

            report.overall_score,

            2,

        ),

        "confidence": round(

            report.confidence,

            2,

        ),

        "category_scores": {

            category.name:

            round(

                category.score,

                2,

            )

            for category in report.categories

        },

        "strengths": report.strengths,

        "weaknesses": report.weaknesses,

        "recommendations": report.recommendations,

    }


# ============================================================
# Public API
# ============================================================

__all__ = [

    "RepositoryType",

    "MetricStatus",

    "Metric",

    "Category",

    "HealthReport",

    "build_health_report",

    "health_dataframe",

    "health_statistics",

]