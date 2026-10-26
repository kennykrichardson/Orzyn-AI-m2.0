"""
============================================================
ORZYN AI m2.0
HTTP Routes
============================================================
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from backend.ai_model import (
    analyze_repository,
)
from backend.code_ai import (
    review_repository,
)
from backend.orzyn import (
    set_active_repository,
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
    set_active_repository(
        request.repository,
    )

    analysis = analyze_repository()

    return asdict(analysis)

@router.post(
    "/code-review",
    tags=["Code"],
)
def code_review(
    request: ReviewRequest,
):
    set_active_repository(
        request.repository,
    )

    try:
        review = review_repository(depth=request.depth)
    except Exception as exc:
        # Keep provider failures inside FastAPI's handled response path so
        # CORSMiddleware can attach CORS headers to the error response.
        message = str(exc)
        if "504" in message or "DEADLINE_EXCEEDED" in message:
            raise HTTPException(
                status_code=504,
                detail=(
                    "Gemini took too long to complete this code review. "
                    "Try Medium review, or configure a currently supported "
                    "Gemini model in the GEMINI_MODEL environment variable."
                ),
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"Code review provider failed: {message[:500]}",
        ) from exc

    return asdict(review)