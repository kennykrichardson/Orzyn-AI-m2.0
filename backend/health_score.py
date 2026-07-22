"""
============================================================
ORZYN AI m2.0
Repository Health Engine
============================================================

Purpose
-------
Evaluate the engineering health of GitHub repositories.

Design Goals
------------
• Explainable scoring
• Rubric based
• Context aware
• Confidence aware
• Backend friendly
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

from backend.commits import CommitProfile
from backend.developer import DeveloperProfile
from backend.issues import IssueProfile
from backend.pull_requests import PullRequestProfile
from backend.repository import RepositoryProfile

# ============================================================
# Repository Types
# ============================================================

class RepositoryType(Enum):

    PERSONAL = "Personal"

    STUDENT = "Student"

    OPEN_SOURCE = "Open Source"

    ENTERPRISE = "Enterprise"

    RESEARCH = "Research"

# ============================================================
# Metric Status
# ============================================================

class MetricStatus(Enum):

    AVAILABLE = "Available"

    MISSING = "Missing"

    NOT_APPLICABLE = "Not Applicable"

# ============================================================
# Metric
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class Metric:

    name: str

    earned: float

    possible: float

    explanation: str

    status: MetricStatus

    evidence: list[str]

# ============================================================
# Category
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class Category:

    name: str

    rubric_weight: float

    metrics: list[Metric]

    explanation: str

    @property
    def earned(self) -> float:

        return sum(

            metric.earned

            for metric in self.metrics

            if metric.status is MetricStatus.AVAILABLE

        )

    @property
    def possible(self) -> float:

        return sum(

            metric.possible

            for metric in self.metrics

            if metric.status is MetricStatus.AVAILABLE

        )

    @property
    def score(self) -> float:

        if self.possible == 0:

            return 0.0

        return (

            self.earned

            /

            self.possible

        ) * 100
    
# ============================================================
# Health Report
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class HealthReport:

    repository: RepositoryProfile

    repository_type: RepositoryType

    overall_score: float

    confidence: float

    categories: list[Category]

    strengths: list[str]

    recommendations: list[str]

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

        return 0.0

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
) -> Metric:

    return Metric(

        name=name,

        earned=earned,

        possible=possible,

        explanation=explanation,

        status=status,

        evidence=evidence or [],

    )


# ============================================================
# Repository Classification
# ============================================================

def classify_repository(
    repository: RepositoryProfile,
    commits: list[CommitProfile],
    developers: list[DeveloperProfile],
) -> RepositoryType:

    contributors = len(developers)

    commit_count = len(commits)

    stars = repository.stars

    forks = repository.forks

    if (

        contributors <= 2

        and

        stars <= 10

        and

        forks <= 2

    ):

        return RepositoryType.PERSONAL

    if (

        contributors <= 5

        and

        stars <= 50

        and

        commit_count <= 500

    ):

        return RepositoryType.STUDENT

    if (

        contributors >= 25

        and

        stars >= 500

    ):

        return RepositoryType.ENTERPRISE

    if (

        contributors >= 10

        or

        stars >= 250

        or

        forks >= 50

    ):

        return RepositoryType.OPEN_SOURCE

    return RepositoryType.RESEARCH


# ============================================================
# Rubrics
# ============================================================

RUBRICS = {

    RepositoryType.PERSONAL: {

        "Repository": 30,

        "Development": 35,

        "Collaboration": 10,

        "Issues": 10,

        "Community": 15,

    },

    RepositoryType.STUDENT: {

        "Repository": 30,

        "Development": 35,

        "Collaboration": 15,

        "Issues": 10,

        "Community": 10,

    },

    RepositoryType.OPEN_SOURCE: {

        "Repository": 20,

        "Development": 25,

        "Collaboration": 25,

        "Issues": 20,

        "Community": 10,

    },

    RepositoryType.ENTERPRISE: {

        "Repository": 20,

        "Development": 20,

        "Collaboration": 25,

        "Issues": 20,

        "Community": 15,

    },

    RepositoryType.RESEARCH: {

        "Repository": 25,

        "Development": 35,

        "Collaboration": 10,

        "Issues": 10,

        "Community": 20,

    },

}


# ============================================================
# Category Factory
# ============================================================

def create_category(
    name: str,
    repository_type: RepositoryType,
    metrics: list[Metric],
    explanation: str,
) -> Category:

    return Category(

        name=name,

        rubric_weight=RUBRICS[repository_type][name],

        metrics=metrics,

        explanation=explanation,

    )


# ============================================================
# Confidence
# ============================================================

def calculate_confidence(
    categories: list[Category],
) -> float:

    total_metrics = 0

    available_metrics = 0

    for category in categories:

        for metric in category.metrics:

            total_metrics += 1

            if metric.status is MetricStatus.AVAILABLE:

                available_metrics += 1

    return percentage(

        available_metrics,

        total_metrics,

    )

# ============================================================
# Repository Metrics
# ============================================================

def build_repository_metrics(
    repository: RepositoryProfile,
) -> list[Metric]:

    metrics: list[Metric] = []

    metrics.append(

        create_metric(

            name="Description",

            earned=10 if repository.description else 0,

            possible=10,

            explanation=(
                "Repository includes a description."
                if repository.description
                else "Repository has no description."
            ),

            evidence=(
                [repository.description]
                if repository.description
                else []
            ),

        )

    )

    metrics.append(

        create_metric(

            name="Default Branch",

            earned=5 if repository.default_branch else 0,

            possible=5,

            explanation=(
                "Default branch configured."
                if repository.default_branch
                else "Default branch unavailable."
            ),

            evidence=(
                [repository.default_branch]
                if repository.default_branch
                else []
            ),

        )

    )

    metrics.append(

        create_metric(

            name="Stars",

            earned=min(repository.stars, 20),

            possible=20,

            explanation=f"{repository.stars} GitHub stars.",

            evidence=[str(repository.stars)],

        )

    )

    metrics.append(

        create_metric(

            name="Forks",

            earned=min(repository.forks, 10),

            possible=10,

            explanation=f"{repository.forks} repository forks.",

            evidence=[str(repository.forks)],

        )

    )

    metrics.append(

        create_metric(

            name="Visibility",

            earned=5,

            possible=5,

            explanation=f"Repository is {repository.visibility}.",

            evidence=[repository.visibility],

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

                name="Commit History",

                earned=0,

                possible=25,

                explanation="No commit history available.",

                status=MetricStatus.MISSING,

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

    metrics: list[Metric] = []

    metrics.append(

        create_metric(

            name="Commit Volume",

            earned=min(commit_count / 10, 10),

            possible=10,

            explanation=f"{commit_count} commits.",

            evidence=[str(commit_count)],

        )

    )

    metrics.append(

        create_metric(

            name="Commit Size",

            earned=10 if average_changes < 500 else 6,

            possible=10,

            explanation=(
                f"Average {average_changes:.1f} changed lines."
            ),

            evidence=[f"{average_changes:.1f}"],

        )

    )

    metrics.append(

        create_metric(

            name="History Availability",

            earned=5,

            possible=5,

            explanation="Commit history successfully analyzed.",

        )

    )

    return metrics


# ============================================================
# Collaboration Metrics
# ============================================================

def build_collaboration_metrics(
    pull_requests: list[PullRequestProfile],
) -> list[Metric]:

    if not pull_requests:

        return [

            create_metric(

                name="Pull Requests",

                earned=0,

                possible=0,

                explanation="No pull request data available.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        ]

    merged = sum(

        pr.merged

        for pr in pull_requests

    )

    total = len(pull_requests)

    merge_rate = merged / total

    return [

        create_metric(

            name="Merge Rate",

            earned=20 * merge_rate,

            possible=20,

            explanation=f"{merged}/{total} pull requests merged.",

            evidence=[f"{merge_rate:.2%}"],

        ),

        create_metric(

            name="PR Activity",

            earned=min(total, 10),

            possible=10,

            explanation=f"{total} pull requests.",

            evidence=[str(total)],

        ),

    ]

# ============================================================
# Issue Metrics
# ============================================================

def build_issue_metrics(
    issues: list[IssueProfile],
) -> list[Metric]:

    if not issues:

        return [

            create_metric(

                name="Issue Tracking",

                earned=0,

                possible=0,

                explanation="No issue data available.",

                status=MetricStatus.NOT_APPLICABLE,

            )

        ]

    closed = sum(

        issue.closed

        for issue in issues

    )

    total = len(issues)

    closure_rate = closed / total

    return [

        create_metric(

            name="Issue Resolution",

            earned=20 * closure_rate,

            possible=20,

            explanation=f"{closed}/{total} issues closed.",

            evidence=[f"{closure_rate:.2%}"],

        ),

        create_metric(

            name="Issue Activity",

            earned=min(total, 10),

            possible=10,

            explanation=f"{total} tracked issues.",

            evidence=[str(total)],

        ),

    ]


# ============================================================
# Community Metrics
# ============================================================

def build_community_metrics(
    developers: list[DeveloperProfile],
) -> list[Metric]:

    contributors = len(developers)

    return [

        create_metric(

            name="Contributors",

            earned=min(contributors * 2, 20),

            possible=20,

            explanation=f"{contributors} contributors.",

            evidence=[str(contributors)],

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

        if category.score >= 80:

            strengths.append(

                f"{category.name} is a strong area."

            )

    if not strengths:

        strengths.append(

            "No major strengths identified."

        )

    return strengths


# ============================================================
# Recommendation Builder
# ============================================================

def build_recommendations(
    categories: list[Category],
) -> list[str]:

    recommendations: list[str] = []

    for category in categories:

        if category.score < 50:

            recommendations.append(

                f"Improve {category.name.lower()} practices."

            )

    if not recommendations:

        recommendations.append(

            "Continue maintaining current engineering quality."

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

            "Repository",

            repository_type,

            build_repository_metrics(
                repository,
            ),

            "Repository quality.",

        ),

        create_category(

            "Development",

            repository_type,

            build_development_metrics(
                commits,
            ),

            "Development activity.",

        ),

        create_category(

            "Collaboration",

            repository_type,

            build_collaboration_metrics(
                pull_requests,
            ),

            "Collaboration quality.",

        ),

        create_category(

            "Issues",

            repository_type,

            build_issue_metrics(
                issues,
            ),

            "Issue management.",

        ),

        create_category(

            "Community",

            repository_type,

            build_community_metrics(
                developers,
            ),

            "Community engagement.",

        ),

    ]

    overall_score = 0.0

    for category in categories:

        overall_score += (

            category.score

            *

            category.rubric_weight

            /

            100

        )

    overall_score = clamp(
        overall_score,
    )

    confidence = calculate_confidence(
        categories,
    )

    strengths = build_strengths(
        categories,
    )

    recommendations = build_recommendations(
        categories,
    )

    return HealthReport(

        repository=repository,

        repository_type=repository_type,

        overall_score=overall_score,

        confidence=confidence,

        categories=categories,

        strengths=strengths,

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

                "Earned": metric.earned,

                "Possible": metric.possible,

                "Score": percentage(

                    metric.earned,

                    metric.possible,

                ),

                "Status": metric.status.value,

                "Explanation": metric.explanation,

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

            category.name: round(

                category.score,

                2,

            )

            for category in report.categories

        },

        "strengths": report.strengths,

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

