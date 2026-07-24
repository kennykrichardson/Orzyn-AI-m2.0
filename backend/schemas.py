"""
============================================================
ORZYN AI m2.0
HTTP Schemas
============================================================
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class HealthResponse(BaseModel):

    status: str

    version: str


class ReviewDepth(str, Enum):

    MEDIUM = "medium"

    DEEP = "deep"


class ReviewRequest(BaseModel):

    repository: str

    depth: ReviewDepth = ReviewDepth.MEDIUM