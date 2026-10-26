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

    try:
        analysis = analyze_repository()
    except Exception as exc:
        message = str(exc)
        normalized = message.lower()
        if any(token in normalized for token in ("http 401", "http 403", "missing cloudflare")):
            status_code = 502
        elif "429" in normalized or "rate limit" in normalized:
            status_code = 429
        elif any(token in normalized for token in ("http 503", "http 500", "http 502", "temporarily unavailable")):
            status_code = 503
        elif "timed out" in normalized or "http 504" in normalized:
            status_code = 504
        else:
            status_code = 502
        raise HTTPException(
            status_code=status_code,
            detail=f"Repository review provider failed: {message[:700]}",
        ) from exc

    return asdict(analysis)

@router.post(
    "/code-review",
    tags=["Code"],
)
def code_review(request: ReviewRequest):
    set_active_repository(request.repository)

    try:
        review = review_repository(depth=request.depth)
    except Exception as exc:
        message = str(exc)
        normalized = message.lower()

        if any(token in normalized for token in ("503", "unavailable", "service_unavailable")):
            raise HTTPException(
                status_code=503,
                detail=(
                    "Cloudflare Workers AI is temporarily unavailable. Orzyn tried its configured "
                    "fallback models, but none completed the review. Retry in a "
                    "minute. If this persists, check Cloudflare Workers AI for model "
                    "access and service status."
                ),
            ) from exc
        if any(token in normalized for token in ("429", "resource_exhausted", "rate limit")):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Cloudflare Workers AI rate or usage limits may have been reached. Check the account's "
                    "quota and billing, then retry after the limit resets."
                ),
            ) from exc
        if any(token in normalized for token in ("504", "deadline_exceeded", "timed out")):
            raise HTTPException(
                status_code=504,
                detail=(
                    "Cloudflare Workers AI could not finish this review before the deadline, even "
                    "after model fallback. Try Medium review or reduce the source "
                    "context sent to the model."
                ),
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"Code review provider failed: {message[:700]}",
        ) from exc

    return asdict(review)
