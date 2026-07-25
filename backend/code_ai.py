"""
============================================================
ORZYN AI m2.0
Source Code Intelligence
============================================================

Purpose
-------
Transforms the deterministic Orzyn analysis pipeline into a
large-language-model architectural review.

This module performs no GitHub discovery.

Instead, it consumes the deterministic backend:

    codebase.py
    analyzer.py
    report.py
    api.py

and produces an expert engineering assessment using an LLM.

The deterministic pipeline remains the source of truth.

The language model is only responsible for interpretation,
reasoning, architectural critique, and recommendations.

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from openai import OpenAI
from backend.engine import (
    report,
)

from backend.codebase import (
    SourceFile,
)

from backend.report import (
    RepositoryReport,
)

from backend.orzyn import (
    OPENROUTER_API_KEY,
    get_active_model,
)

from backend.schemas import ReviewDepth

# ============================================================
# Constants
# ============================================================

PROMPT_VERSION = "2.0.0"

SECTION_SEPARATOR = "\n\n"

MEDIUM_REVIEW_BUDGET = 1500

DEEP_REVIEW_BUDGET = 4000

DEFAULT_TIMEOUT = 120

# ============================================================
# Response Models
# ============================================================

@dataclass(
    slots=True,
    frozen=True,
)
class CodeAIResponse:

    provider: str

    model: str

    prompt: str

    response: str

    raw: Any


@dataclass(
    slots=True,
    frozen=True,
)
class CodeReview:

    report: RepositoryReport

    response: CodeAIResponse

# ============================================================
# Prompt Builder
# ============================================================

class PromptBuilder:

    def __init__(
        self,
        report: RepositoryReport,
        depth: ReviewDepth,
    ):

        self.repository_report = report

        self.analysis = report.analysis

        self.codebase = report.analysis.codebase

        self.depth = depth

    @staticmethod
    def section(
        title: str,
        body: str,
    ) -> str:

        return f"""
{title}
{'=' * len(title)}

{body.strip()}
""".strip()

    @staticmethod
    def bullet(
        values: list[str],
    ) -> str:

        if not values:

            return "None"

        return "\n".join(

            f"• {value}"

            for value in values

        )

    @staticmethod
    def kv(
        **kwargs: object,
    ) -> str:

        return "\n".join(

            f"{key}: {value}"

            for key, value in kwargs.items()

        )

    @staticmethod
    def system_prompt() -> str:

        return """
You are Orzyn AI.

You are a Principal Software Architect performing an expert engineering review.

You are NOT responsible for discovering repository information.

A deterministic analysis pipeline has already extracted repository metadata, project statistics, engineering metrics, analyzer results, and representative source files.

Treat the deterministic analysis as the authoritative source of truth.

Your responsibility is to:

• interpret deterministic findings
• explain architectural implications
• identify engineering tradeoffs
• prioritize improvements
• communicate clearly and accurately

Rules

1. Never invent files.

2. Never invent APIs, endpoints, frameworks, libraries, classes, functions, or execution paths.

3. Never assume relationships that are not explicitly visible.

4. If evidence is insufficient, explicitly state that the information cannot be determined from the supplied repository.

5. Every architectural conclusion must be supported by deterministic evidence or representative source code.

6. Do not contradict deterministic findings.

7. Recommendations must be directly connected to observed evidence.

8. Do not recommend technologies unless they solve a demonstrated problem.

9. Distinguish clearly between:

Observed
Inferred
Recommendation

10. Preserve good engineering decisions. Do not recommend replacing existing architecture without evidence.

Your review should read like an experienced software architect reviewing a production codebase for another senior engineer.

Accuracy is more important than completeness.

Evidence is more important than speculation.
""".strip()

    # ========================================================
    # Repository
    # ========================================================

    def repository(
        self,
    ) -> str:

        metadata = self.codebase.metadata

        statistics = self.codebase.statistics

        return self.section(

            "Repository",

            self.kv(

                Owner=metadata.owner,

                Repository=metadata.name,

                Description=metadata.description,

                Homepage=metadata.homepage,

                Default_Branch=metadata.default_branch,

                Repository_Type=self.codebase.repository_type.value,

                Framework=self.codebase.framework,

                Primary_Language=self.codebase.primary_language,

                Stars=metadata.stars,

                Forks=metadata.forks,

                Total_Files=statistics.total_files,

                Supported_Files=statistics.supported_files,

                Ignored_Files=statistics.ignored_files,

                Selected_Files=len(

                    self.codebase.files,

                ),

            ),

        )

    # ========================================================
    # Manifest Files
    # ========================================================

    def manifests(
        self,
    ) -> str:

        manifests = self.codebase.manifests

        return self.section(

            "Manifest Files",

            self.kv(

                Package_JSON=manifests.package_json,

                PyProject=manifests.pyproject,

                Requirements=manifests.requirements,

                Cargo=manifests.cargo,

                Go_Mod=manifests.go_mod,

                Maven=manifests.pom,

                Gradle=manifests.gradle,

                Flutter=manifests.flutter,

            ),

        )

    # ========================================================
    # Repository Statistics
    # ========================================================

    def statistics(
        self,
    ) -> str:

        distribution = [

            f"{language}: {count}"

            for language, count

            in sorted(

                self.codebase.statistics
                .language_distribution.items()

            )

        ]

        body = [

            self.kv(

                Total_Files=self.codebase.statistics.total_files,

                Supported_Files=self.codebase.statistics.supported_files,

                Ignored_Files=self.codebase.statistics.ignored_files,

            ),

            "Language Distribution",

            self.bullet(

                distribution,

            ),

        ]

        return self.section(

            "Repository Statistics",

            SECTION_SEPARATOR.join(

                body,

            ),

        )

    # ========================================================
    # Analysis
    # ========================================================

    def analysis_summary(
        self,
    ) -> str:

        analysis = self.analysis

        health = analysis.health_report

        return self.section(

            "Analysis",

            self.kv(

                Overall_Score=analysis.overall_score,

                Health_Score=round(health.overall_score, 2),

                Confidence=round(health.confidence, 2),

                Repository_Type=health.repository_type.value,

                Strengths=len(health.strengths),

                Weaknesses=len(health.weaknesses),

                Recommendations=len(health.recommendations),

                Execution_Time_MS=analysis.execution_time_ms,

                Analyzer_Count=len(analysis.analyzers),

            ),

        )


    # ========================================================
    # Analyzer Results
    # ========================================================

    def analyzers(
        self,
    ) -> str:

        blocks: list[str] = []

        for result in self.analysis.analyzers:

            payload = result.payload

            blocks.append(

                self.section(

                    result.name,

                    self.kv(

                        Duration_MS=result.duration_ms,

                        Result=payload,

                    ),

                )

            )

        return self.section(

            "Registered Analyzers",

            SECTION_SEPARATOR.join(

                blocks,

            ),

        )

    # ========================================================
    # Repository Report
    # ========================================================

    def report_sections(
        self,
    ) -> str:

        blocks: list[str] = []

        for section in self.repository_report.sections:

            blocks.append(

                self.section(

                    section.title,

                    str(

                        section.data,

                    ),

                )

            )

        return self.section(

            "Deterministic Report",

            SECTION_SEPARATOR.join(

                blocks,

            ),

        )

    # ========================================================
    # Representative Source File
    # ========================================================

    def source_file(
        self,
        source: SourceFile,
        remaining_budget: int,
    ) -> tuple[str, int]:

        content = source.content.strip()

        estimated_tokens = len(content) // 4

        imports = self.bullet(

            list(source.imports[:5]),

        )

        language = (

            source.language.lower()

            if source.language

            else "text"

        )

        if estimated_tokens > remaining_budget:

            allowed_chars = remaining_budget * 4

            content = content[:allowed_chars]

            estimated_tokens = remaining_budget

            if allowed_chars < len(source.content):

                content += "\n\n...<truncated>..."

        block = f"""
File
====

Path
{source.path}

Language
{source.language}

Priority
{source.priority:.2f}

Size
{source.size} bytes

Imports

{imports}

Source

```{language}
{content}
```
""".strip()

        return(

            block, 

            remaining_budget - estimated_tokens,
        )

    # ========================================================
    # Representative Source Files
    # ========================================================

    def source_files(
        self,
    ) -> str:

        budget = (

            MEDIUM_REVIEW_BUDGET

            if self.depth is ReviewDepth.MEDIUM

            else

            DEEP_REVIEW_BUDGET

        )

        remaining_budget = budget

        sections = []

        files = sorted(

            self.codebase.files,

            key=lambda file: file.priority,

            reverse=True,

        )

        for source in files:

            if remaining_budget <= 0:

                break

            section, remaining_budget = self.source_file(

                source,

                remaining_budget,

            )

            sections.append(

                section,
 
            )

        return self.section(
    
            "Representative Source Files",

            SECTION_SEPARATOR.join(

                sections,

            ),

        )

    # ========================================================
    # Final Prompt
    # ========================================================

    def build(
        self,
    ) -> str:

        sections = [

            self.repository(),

            self.manifests(),

            self.statistics(),

            self.analysis_summary(),

            self.analyzers(),

        ]

        if self.depth is ReviewDepth.DEEP:

            sections.append(

                self.report_sections(),

            )
     
        sections.append(

            self.source_files(),

        )

        sections.append(

            TASK_PROMPT,

        )

        return SECTION_SEPARATOR.join(

            sections,

        )
# ============================================================
# Task Prompt
# ============================================================

TASK_PROMPT = """
Perform a complete engineering review using ONLY the supplied deterministic analysis and representative source files.

The deterministic report is authoritative.

Never contradict it.

If evidence is missing, explicitly state that the information cannot be determined.

Structure your review exactly as follows.

# 1. Executive Summary

• Explain what the repository appears to do.
• Summarize overall engineering quality.
• Mention the deterministic health score.
• Mention repository classification.

# 2. Architecture

For every architectural statement:

• describe the observation
• provide supporting evidence
• explain why it matters

Do not invent components.

Do not invent execution paths.

Do not invent REST endpoints.

Do not infer internal behavior without source-code evidence.

# 3. Data Flow

Only describe execution flow that is directly observable.

If complete execution flow cannot be determined from the supplied files, explicitly state that limitation.

# 4. Engineering Assessment

Evaluate:

• Code Organization
• Separation of Concerns
• Maintainability
• Readability
• Modularity
• Extensibility
• Dependency Management
• Error Handling

Every subsection must include:

Observation

Evidence

Impact

# 5. Engineering Strengths

List engineering decisions that should be preserved.

Support every strength with evidence.

# 6. Engineering Weaknesses

Identify architectural problems, technical debt and maintainability issues.

Every weakness must include:

Observation

Evidence

Impact

Avoid generic criticism.

# 7. Risks

Separate risks into:

Critical

High

Medium

Low

Only include risks supported by repository evidence.

# 8. Prioritized Recommendations

Order recommendations from highest impact to lowest.

For every recommendation include:

Problem

Evidence

Recommendation

Expected Benefit

Do not recommend frameworks or technologies unless they directly solve an identified problem.

Avoid generic recommendations such as:

"Add logging"

"Use Flask"

"Use Docker"

unless deterministic evidence clearly justifies them.

Keep recommendations specific to this repository.

Throughout the review:

Never invent information.

Never speculate.

Never contradict deterministic analysis.

Every engineering conclusion should be traceable back to supplied evidence.
""".strip()

# ============================================================
# AI Inference
# ============================================================

class CodeInference:

    def __init__(
        self,
        model: str | None = None,
    ):

        self.config = get_active_model()

        self.provider = self.config.provider

        self.model = model or self.config.model

        self.client = self._create_client()

    def _create_client(
        self,
    ) -> OpenAI:

        if self.provider != "openrouter":

            raise ValueError(

                f"Unsupported provider: {self.provider}"

            )

        return OpenAI(

            api_key=OPENROUTER_API_KEY,

            base_url="https://openrouter.ai/api/v1",

        )

    def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> CodeAIResponse:

        completion = (

            self.client.chat.completions.create(

                model=self.model,

                messages=[

                    {

                        "role": "system",

                        "content": PromptBuilder.system_prompt(),

                    },

                    {

                        "role": "user",

                        "content": prompt,

                    },

                ],

                temperature=self.config.temperature,

                top_p=self.config.top_p,

                max_tokens=self.config.max_tokens,

                **kwargs,

            )

        )

        message = (

            completion

            .choices[0]

            .message

            .content

        )

        return CodeAIResponse(

            provider=self.provider,

            model=self.model,

            prompt=prompt,

            response=message,

            raw=completion,

        )

# ============================================================
# Code AI
# ============================================================

class CodeAI:

    def __init__(
        self,
        model: str | None = None,
    ):

        self.inference = CodeInference(
            model=model,
        )

    # ========================================================
    # Prompt Utilities
    # ========================================================

    @staticmethod
    def prompt(
        report: RepositoryReport,
        depth: ReviewDepth = ReviewDepth.MEDIUM,
    ) -> str:

        """
        Build the complete user prompt without
        executing inference.

        Useful for debugging prompt construction
        and inspecting the context sent to the LLM.
        """

        return PromptBuilder(
            report,
            depth,
        ).build()

    @staticmethod
    def system_prompt(
    ) -> str:

        """
        Return the system prompt used for every
        repository review.
        """

        return PromptBuilder.system_prompt()

    # ========================================================
    # Review Existing Report
    # ========================================================

    def review(
        self,
        report: RepositoryReport,
        depth: ReviewDepth = ReviewDepth.MEDIUM,
        **kwargs,
    ) -> CodeReview:

        """
        Perform an architectural review using an
        existing deterministic RepositoryReport.
        """

        prompt = self.prompt(
            report,
            depth,
        )

        response = self.inference.generate(

            prompt,

            **kwargs,

        )

        return CodeReview(

            report=report,

            response=response,

        )

    # ========================================================
    # Review Active Repository
    # ========================================================

    def review_repository(
        self,
        depth: ReviewDepth = ReviewDepth.MEDIUM,
        **kwargs,
    ) -> CodeReview:

        """
        Execute the complete deterministic Orzyn
        pipeline before performing the AI review.

        GitHub
            ↓
        Codebase
            ↓
        Analysis
            ↓
        RepositoryReport
            ↓
        LLM Review
        """

        repository_report = report()

        return self.review(

            repository_report,

            depth=depth,

            **kwargs,

        )

# ============================================================
# Default Instance
# ============================================================

_DEFAULT_CODE_AI = CodeAI()


# ============================================================
# Public API
# ============================================================

def review(
    report: RepositoryReport,
    depth: ReviewDepth = ReviewDepth.MEDIUM,
    **kwargs,
) -> CodeReview:

    return _DEFAULT_CODE_AI.review(

        report,

        depth=depth,

        **kwargs,

    )

def review_repository(
    depth: ReviewDepth = ReviewDepth.MEDIUM,
    **kwargs,
) -> CodeReview:

    """
    Execute the complete deterministic Orzyn
    pipeline and perform an AI review of the
    active repository.
    """

    return _DEFAULT_CODE_AI.review_repository(

        depth=depth,

        **kwargs,

    )


def build_prompt(
    report: RepositoryReport,
    depth: ReviewDepth = ReviewDepth.MEDIUM,
) -> str:

    """
    Build the complete prompt without contacting
    the language model.

    Intended for debugging and prompt inspection.
    """

    return CodeAI.prompt(

        report,

        depth,

    )


def system_prompt(
) -> str:

    """
    Return the global system prompt used for all
    repository reviews.
    """

    return CodeAI.system_prompt()

# ============================================================
# Version
# ============================================================

CODE_AI_VERSION = "2.0.0"

# ============================================================
# Exports
# ============================================================

__all__ = [

    "PROMPT_VERSION",

    "CODE_AI_VERSION",

    "CodeAIResponse",

    "CodeReview",

    "PromptBuilder",

    "CodeInference",

    "CodeAI",

    "review",

    "review_repository",

    "build_prompt",

    "system_prompt",

]