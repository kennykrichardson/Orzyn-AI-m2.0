# ============================================================
# ORZYN AI m2.0
# AI Models
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from huggingface_hub import InferenceClient

from backend.commits import (
    CommitProfile,
    fetch_commits,
)

from backend.developer import (
    DeveloperProfile,
    fetch_developers,
)

from backend.health_score import (
    HealthReport,
    build_health_report,
)

from backend.issues import (
    IssueProfile,
    fetch_issues,
)

from backend.pull_requests import (
    PullRequestProfile,
    fetch_pull_requests,
)

from backend.repository import (
    RepositoryProfile,
    fetch_repository_profile,
)

from backend.orzyn import (
    HF_TOKEN,
    get_active_model,
    get_active_repository,
)

# ============================================================
# Constants
# ============================================================

PROMPT_VERSION = "2.0"

DEFAULT_TEMPERATURE = 0.2

DEFAULT_MAX_TOKENS = 1200

DEFAULT_TOP_P = 0.95

DEFAULT_TIMEOUT = 60

# ============================================================
# AI Response
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class AIResponse:

    provider: str

    model: str

    prompt: str

    response: str

    raw: Any


# ============================================================
# Repository Analysis
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class AIAnalysis:

    repository: RepositoryProfile

    commits: list[CommitProfile]

    pull_requests: list[PullRequestProfile]

    issues: list[IssueProfile]

    developers: list[DeveloperProfile]

    health: HealthReport

    response: AIResponse


# ============================================================
# AI Inference
# ============================================================

class AIInference:

    def __init__(
        self,
        model: str | None = None,
    ):

        config = get_active_model()

        self.provider = config.provider

        self.model = model or config.model

        self.client = InferenceClient(

            api_key=HF_TOKEN,

            timeout=DEFAULT_TIMEOUT,

        )

    def generate(
        self,
        prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        top_p: float = DEFAULT_TOP_P,
        **kwargs: Any,
    ) -> AIResponse:

        if self.provider != "huggingface":

            raise ValueError(

                f"Unsupported provider: {self.provider}"

            )

        try:

            completion = self.client.chat.completions.create(

                model=self.model,

                messages=[
                    {
                        "role": "system",
                        "content": build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],

                temperature=temperature,

                max_tokens=max_tokens,

                top_p=top_p,

                **kwargs,

            )

        except Exception as exc:
            print(type(exc).__name__)
            print(exc)
            raise

        response = completion.choices[0].message.content

        return AIResponse(

            provider=self.provider,

            model=self.model,

            prompt=prompt,

            response=response,

            raw=completion,

        )
    
# ============================================================
# Prompt Builders
# ============================================================

def build_system_prompt() -> str:

    return """
You are Orzyn AI.

You are a senior software architect and code reviewer.

Base every conclusion ONLY on the supplied repository data.

Do not invent information.

If evidence is missing, explicitly say so.

Provide concise, technical, actionable feedback.

Never hallucinate repository features.
""".strip()


def build_repository_prompt(
    repository: RepositoryProfile,
) -> str:

    active_repo = get_active_repository()

    return f"""
Repository

Name: {repository.name}
Owner: {active_repo.owner}
Description: {repository.description or "None"}

Language: {repository.primary_language or "Unknown"}
Visibility: {repository.visibility}

Stars: {repository.stars}
Forks: {repository.forks}
Watchers: {repository.watchers}

Default Branch: {repository.default_branch}
""".strip()


def build_commit_prompt(
    commits: list[CommitProfile],
) -> str:

    if not commits:

        return """
Development

No commit history available.
""".strip()

    largest_commit = max(

        commits,

        key=lambda commit:

        commit.additions +

        commit.deletions,

    )

    total_changes = sum(

        commit.additions +

        commit.deletions

        for commit in commits

    )

    return f"""
Development

Commits: {len(commits)}

Total Changes: {total_changes}

Largest Commit

Message: {largest_commit.message}

Changed Lines:

{largest_commit.additions + largest_commit.deletions}
""".strip()


def build_collaboration_prompt(
    developers: list[DeveloperProfile],
    pull_requests: list[PullRequestProfile],
    issues: list[IssueProfile],
) -> str:

    merged_prs = sum(

        pr.merged

        for pr in pull_requests

    )

    closed_issues = sum(

        issue.closed

        for issue in issues

    )

    return f"""
Collaboration

Contributors: {len(developers)}

Pull Requests: {len(pull_requests)}

Merged Pull Requests: {merged_prs}

Issues: {len(issues)}

Closed Issues: {closed_issues}
""".strip()


def build_health_prompt(
    report: HealthReport,
) -> str:

    categories = "\n".join(

        f"- {category.name}: {category.score:.1f}"

        for category in report.categories

    )

    strengths = "\n".join(

        f"- {strength}"

        for strength in report.strengths

    )

    recommendations = "\n".join(

        f"- {recommendation}"

        for recommendation in report.recommendations

    )

    return f"""
Repository Health

Overall Score: {report.overall_score:.1f}

Confidence: {report.confidence:.1f}

Repository Type:

{report.repository_type.value}

Category Scores

{categories}

Strengths

{strengths}

Recommendations

{recommendations}
""".strip()


# ============================================================
# User Prompt
# ============================================================

def build_user_prompt(
    repository: RepositoryProfile,
    commits: list[CommitProfile],
    pull_requests: list[PullRequestProfile],
    issues: list[IssueProfile],
    developers: list[DeveloperProfile],
    health: HealthReport,
) -> str:

    sections = [

        build_repository_prompt(
            repository,
        ),

        build_commit_prompt(
            commits,
        ),

        build_collaboration_prompt(
            developers,
            pull_requests,
            issues,
        ),

        build_health_prompt(
            health,
        ),

        """
Task

Write a professional engineering review of this repository.

Structure the report as:

1. Executive Summary

2. Repository Overview

3. Development Activity

4. Collaboration

5. Strengths

6. Weaknesses

7. Recommendations

Only reference the supplied repository information.

Do not invent facts.

State when information is unavailable.
""".strip(),

    ]

    return "\n\n".join(sections)

# ============================================================
# Repository Analysis
# ============================================================

def analyze_repository(
    repository: RepositoryProfile | None = None,
    commits: list[CommitProfile] | None = None,
    pull_requests: list[PullRequestProfile] | None = None,
    issues: list[IssueProfile] | None = None,
    developers: list[DeveloperProfile] | None = None,
    model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    top_p: float = DEFAULT_TOP_P,
    **kwargs: Any,
) -> AIAnalysis:

    repository = repository or fetch_repository_profile()

    commits = commits or fetch_commits()

    pull_requests = (

        pull_requests

        or

        fetch_pull_requests()

    )

    issues = issues or fetch_issues()

    developers = (

        developers

        or

        fetch_developers()

    )

    health = build_health_report(

        repository,

        commits,

        pull_requests,

        issues,

        developers,

    )

    prompt = build_user_prompt(

        repository,

        commits,

        pull_requests,

        issues,

        developers,

        health,

    )

    inference = AIInference(

        model=model,

    )

    response = inference.generate(

        prompt=prompt,

        temperature=temperature,

        max_tokens=max_tokens,

        top_p=top_p,

        **kwargs,

    )

    return AIAnalysis(

        repository=repository,

        commits=commits,

        pull_requests=pull_requests,

        issues=issues,

        developers=developers,

        health=health,

        response=response,

    )


# ============================================================
# Public API
# ============================================================

__all__ = [

    "AIResponse",

    "AIAnalysis",

    "AIInference",

    "build_system_prompt",

    "build_repository_prompt",

    "build_commit_prompt",

    "build_collaboration_prompt",

    "build_health_prompt",

    "build_user_prompt",

    "analyze_repository",

]