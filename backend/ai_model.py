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

DEFAULT_TEMPERATURE = 0.2

DEFAULT_MAX_TOKENS = 1000

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

        self.client = InferenceClient(

            api_key=HF_TOKEN,
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
            raise RuntimeError(
                f"AI inference failed: {exc}"
            ) from exc

        message = completion.choices[0].message

        if not message.content:
            raise RuntimeError(
                f"Model produced no final answer. "
                f"finish_reason={completion.choices[0].finish_reason}, "
                f"reasoning_length={len(message.reasoning or '')}"
            )

        response = message.content

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
The Repository Metadata and Repository Health sections are deterministic backend results.

Do not reinterpret or contradict them.

Instead, use them as evidence when writing the Engineering Assessment.

Your role is to explain, connect, and interpret the supplied evidence rather than recomputing it.
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
You are Orzyn AI, a senior software architect.

Do not output or spend tokens on internal reasoning.

Return only the final repository review.

Begin immediately with "Executive Summary".

The supplied repository analysis is authoritative.

Explain the evidence.

Never invent missing information.

Do not contradict supplied metrics.

Keep recommendations practical and evidence-based.

If information cannot be determined, explicitly say so.

Return the review using Markdown.

Use these exact section headings.

# Executive Summary

# Engineering Assessment

# Strengths

# Weaknesses

# Recommendations

Do not number the headings.

Do not use the symbol '*' at any cost, and only use Markdown headings.

Use Markdown headings only.

Do not output JSON.

Do not output tables unless necessary.

Keep paragraphs concise.
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

    category_scores = "\n".join(

        f"{category.name}: {category.score:.1f}"

        for category in report.categories

    )

    strengths = bullet_list(

        report.strengths,

    )

    weaknesses = bullet_list(

        report.weaknesses,

    )

    recommendations = bullet_list(

        report.recommendations,

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

Category Scores

{category_scores}

Strengths

{strengths}

Weaknesses

{weaknesses}

Recommendations

{recommendations}
""".strip(),

    )

PROMPT_BUILDERS = (

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