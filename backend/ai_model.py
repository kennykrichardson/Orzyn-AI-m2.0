# ============================================================
# ORZYN AI m2.0
# AI Models
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

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
    OPENROUTER_API_KEY,
    get_active_model,
    get_active_repository,
)

# ============================================================
# Constants
# ============================================================

PROMPT_VERSION = "2.0"

DEFAULT_TEMPERATURE = 0.2

DEFAULT_MAX_TOKENS = 600

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
# Prompt Context
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class PromptContext:

    repository: RepositoryProfile

    commits: list[CommitProfile]

    pull_requests: list[PullRequestProfile]

    issues: list[IssueProfile]

    developers: list[DeveloperProfile]

    health: HealthReport

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

        self.client = OpenAI(

            api_key=OPENROUTER_API_KEY,

            base_url="https://openrouter.ai/api/v1",

        )

    def generate(
        self,
        prompt: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        top_p: float = DEFAULT_TOP_P,
        **kwargs: Any,
    ) -> AIResponse:

        if self.provider != "openrouter":

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

# ============================================================
# Prompt Helpers
# ============================================================

SECTION_SEPARATOR = "\n\n"

TASK_PROMPT = """
Task

Produce a professional engineering review.

The backend has already completed the technical analysis.

Your responsibility is to explain the supplied evidence.

Repository Purpose

Begin the Repository Overview with a detailed explanation of the repository's purpose.

The Repository Overview should be approximately one well-developed paragraph spanning at least three to five sentences.

Start with the supplied repository description as the primary source of truth.

Expand naturally using the repository name, primary language, repository type, framework, detected technologies, and other deterministic metadata supplied by the backend.

Describe what problem the repository solves, who it appears to be built for, how its major technologies support that purpose, and the overall engineering direction of the project.

Do not invent functionality that is not supported by the supplied evidence.

If the repository description is missing, explicitly state that no description was provided and infer only high-level purpose from deterministic metadata such as repository name, framework, primary language, and repository classification.

The Repository Overview should read like the opening section of a professional architecture review rather than a short GitHub description.

Report Structure

1. Executive Summary

2. Repository Overview

3. Development Analysis

4. Repository Health

5. Engineering Strengths

6. Engineering Weaknesses

7. Engineering Recommendations

Writing Rules

• Base every statement on supplied evidence.

• Never speculate.

• Never invent repository features.

• Never infer developer intent.

• Never infer commit purpose.

• Respect the repository type.

• Ignore Not Applicable metrics.

• Explain why scores were assigned.

• Explain confidence.

• Keep recommendations specific.

• If no improvement is justified, explicitly state that current engineering practices should be maintained.

Tone

Write like a senior software architect reviewing a production codebase.

Be concise.

Avoid repetition.

Avoid generic advice.

Interpret backend findings.

Do not reinterpret backend scoring logic.

Do not justify a score using assumptions that were not explicitly supplied.
""".strip()

def section(
    title: str,
    body: str,
) -> str:
    """
    Creates a consistently formatted prompt section.
    """

    return f"""
{title}
{'=' * len(title)}

{body.strip()}
""".strip()


def bullet_list(
    items: list[str],
    empty: str = "None",
) -> str:
    """
    Formats a list as bullet points.
    """

    if not items:
        return empty

    return "\n".join(

        f"• {item}"

        for item in items

    )


def kv(
    **values: object,
) -> str:
    """
    Formats key-value pairs.

    Example

    Name: Orzyn
    Stars: 12
    """

    return "\n".join(

        f"{key}: {value}"

        for key, value in values.items()

    )

def build_system_prompt() -> str:

    return """
You are Orzyn AI.

You are a Senior Software Architect performing an engineering review.

The backend has already analyzed the repository.

The backend computed all engineering metrics.

Your job is to explain them.

Do NOT recompute scores.

Do NOT infer technologies, files, architecture, testing, CI/CD, documentation or engineering practices that were not supplied.

The repository description, homepage, repository name, and all backend-computed metrics are trusted evidence.

You may summarize or rephrase this information naturally.

Do not invent functionality beyond the supplied evidence.

Never speculate.

Never guess.

Never fabricate.

Always separate:

• Evidence
• Observation
• Recommendation

Repository Type matters.

For Personal repositories:

- Do not recommend Git Flow.
- Do not recommend pull requests.
- Do not recommend multiple contributors.
- Do not recommend issue tracking unless backend evidence supports it.
- Treat Not Applicable metrics as neutral, never negative.

Commit Analysis Rules

- Never infer the purpose of a commit.
- Never infer developer intent.
- Never infer project history.
- Never infer architecture changes.
- Never infer feature additions.
- Never infer refactoring.

Discuss only measurable facts supplied by the backend.

If a commit is unusually large, simply state its measured size and explain how large commits generally affect maintainability without assuming why they occurred.

Health Score Rules

- Explain why the backend assigned the score.
- Do not reinterpret backend scores.
- Do not contradict backend findings.

Recommendations

Recommendations must originate from supplied evidence.

Avoid generic GitHub advice.

If insufficient evidence exists, explicitly state that no recommendation is necessary.
""".strip()


def build_repository_prompt(
    context: PromptContext,
) -> str:

    active_repo = get_active_repository()

    repository = context.repository

    return section(

        "Repository",

        kv(

            Name=repository.name,

            Owner=active_repo.owner,

            Description=repository.description or "None",

            Primary_Language=repository.primary_language or "Unknown",

            Visibility=repository.visibility,

            Homepage=repository.homepage or "None",

            Stars=repository.stars,

            Forks=repository.forks,

            Watchers=repository.watchers,

            Default_Branch=repository.default_branch,

            Repository_Type=context.health.repository_type.value,

        ),

    )


def build_commit_prompt(
    context: PromptContext,
) -> str:

    commits = context.commits

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

    average = total_changes / len(commits)

    largest_commit_size = (

        largest_commit.additions +

        largest_commit.deletions

    )

    return section(

        "Development",

        kv(

            Commits=len(commits),

            Total_Changes=total_changes,

            Average_Commit_Size=f"{average:.1f} changed lines",

            Largest_Commit=largest_commit.message,

            Largest_Commit_Size=f"{largest_commit_size} changed lines",

        ),

    )

def build_collaboration_prompt(
        context: PromptContext,
) -> str:

    developers = context.developers

    pull_requests = context.pull_requests

    issues = context.issues

    merged_prs = sum(

        pr.merged

        for pr in pull_requests

    )

    closed_issues = sum(

        issue.closed

        for issue in issues

    )

    return section(

        "Collaboration",

        kv(

            Contributors=len(developers),

            Pull_Requests=len(pull_requests),

            Merged_Pull_Requests=merged_prs,

            Issues=len(issues),

            Closed_Issues=closed_issues,

        ),

    )

def build_health_prompt(
    context: PromptContext,
) -> str:

    report = context.health

    category_blocks = []

    for category in report.categories:

        metric_lines = []

        for metric in category.metrics:

            metric_lines.append(

                f"""\
• {metric.name}
  Score: {metric.score:.1f}
  Status: {metric.status.value}
  Explanation: {metric.explanation}
"""

            )

        category_blocks.append(

            f"""
{category.name}

Category Score:
{category.score:.1f}

{chr(10).join(metric_lines)}
""".strip()

        )

    strengths = bullet_list(

        report.strengths,

    )

    weaknesses = bullet_list(

        report.weaknesses

    )

    recommendations = bullet_list(

        report.recommendations

    )

    return section(

    "Repository Health",

    f"""
Overall Score:
{report.overall_score:.1f}

Confidence:
{report.confidence:.1f}

Repository Type:
{report.repository_type.value}

Repository Classification

This repository was classified by the backend.

Metrics marked Not Applicable were excluded from scoring.

Do not criticize excluded metrics.

Category Analysis

{chr(10).join(category_blocks)}

Strengths

{strengths}

Weaknesses

{weaknesses}

Recommendations

{recommendations}
""".strip(),

)

PROMPT_BUILDERS = (

    build_repository_prompt,

    build_commit_prompt,

    build_collaboration_prompt,

    build_health_prompt,

)
# ============================================================
# User Prompt
# ============================================================

def build_user_prompt(
        context: PromptContext,
) -> str:

    sections = [

        builder(context)

        for builder in PROMPT_BUILDERS

    ]

    sections.append(

        TASK_PROMPT,

    )

    return SECTION_SEPARATOR.join(

        sections,

    )

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

    context = PromptContext(

        repository=repository,

        commits=commits,

        pull_requests=pull_requests,

        issues=issues,

        developers=developers,

        health=health,

)

    prompt = build_user_prompt(
        context,
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

    "PromptContext",

    "TASK_PROMPT",

]