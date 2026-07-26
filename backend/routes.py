"""
============================================================
ORZYN AI m2.0
HTTP Routes
============================================================
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from backend.ai_model import (
    analyze_repository,
)
from backend.code_ai import (
    review_repository,
)

from backend.schemas import (
    HealthResponse,
    ReviewRequest,
    ReviewDepth,
)

router = APIRouter()


@router.get(
    "/",
    tags=["General"],
)
def index() -> dict[str, str]:

    return {

        "name": "Orzyn AI",

        "version": "2.0.0",

        "status": "running",

    }


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
)
def health() -> HealthResponse:

    return HealthResponse(

        status="ok",

        version="2.0.0",
   
    )    

@router.post(
    "/repository-review",
    tags=["Repository"],
)
def repository_review(
    request: ReviewRequest,
):
    analysis = analyze_repository()

    return asdict(analysis)

@router.post(
    "/code-review",
    tags=["Code"],
)
def code_review(
    request: ReviewRequest,
):

    review = review_repository(

        depth=ReviewDepth.MEDIUM,

    )

    return asdict(

        review,

    )

@router.post(
    "/deep-code-review",
    tags=["Code"],
)
def deep_code_review(
    request: ReviewRequest,
):

    review = review_repository(

        depth=ReviewDepth.DEEP,

    )

    return asdict(

        review,

    )