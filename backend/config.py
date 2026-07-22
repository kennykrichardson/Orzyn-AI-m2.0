"""
============================================================
ORZYN AI m2.0
Configuration
============================================================

Purpose
-------
Centralized project configuration.

Responsibilities
----------------
• Load environment variables
• Define project paths
• Configure GitHub GraphQL endpoint
• Configure HuggingFace endpoint
• Verify project directories
• Provide reusable configuration for every notebook

Author
------
Kenny Richardson

Project
-------
Orzyn AI m2.0
"""



from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv



# ---------------------------------------------------------
# Project Root
# ---------------------------------------------------------

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

BACKEND_DIR: Final[Path] = PROJECT_ROOT / "backend"

DATA_DIR: Final[Path] = BACKEND_DIR / "data"

CACHE_DIR: Final[Path] = BACKEND_DIR / "cache"

EXPORT_DIR: Final[Path] = BACKEND_DIR / "exports"

MODEL_DIR: Final[Path] = BACKEND_DIR / "models"

ENV_FILE: Final[Path] = PROJECT_ROOT / ".env"



DIRECTORIES = (
    DATA_DIR,
    CACHE_DIR,
    EXPORT_DIR,
    MODEL_DIR,
)

for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)



if not load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
):
    raise FileNotFoundError(
        f"Unable to load environment file:\n{ENV_FILE}"
    )

GITHUB_GRAPHQL_URL: Final = "https://api.github.com/graphql"

GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN")



HF_TOKEN: str | None = os.getenv("HF_TOKEN")



GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/vnd.github+json",
}

HF_HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}



# ---------------------------------------------------------
# FastAPI Configuration
# ---------------------------------------------------------

API_PREFIX: Final[str] = "/api/v1"

HOST: Final[str] = os.getenv("HOST", "0.0.0.0")

PORT: Final[int] = int(os.getenv("PORT", "8000"))

DEBUG: Final[bool] = os.getenv("DEBUG", "False").lower() == "true"

FRONTEND_URL: Final[str] = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

DEFAULT_AI_PROVIDER: Final[str] = os.getenv(
    "DEFAULT_AI_PROVIDER",
    "huggingface",
)

DEFAULT_MODEL: Final[str] = os.getenv(
    "DEFAULT_MODEL",
    "Qwen/Qwen2.5-7B-Instruct",
)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_environment() -> None:
    """
    Validate the backend configuration.

    Raises
    ------
    FileNotFoundError
        If the .env file cannot be located.

    RuntimeError
        If required secrets are missing.
    """

    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f".env file not found:\n{ENV_FILE}"
        )

    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Missing environment variable: GITHUB_TOKEN"
        )

    if not HF_TOKEN:
        raise RuntimeError(
            "Missing environment variable: HF_TOKEN"
        )

    for directory in DIRECTORIES:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

CONFIG = {
    "project_root": PROJECT_ROOT,
    "backend": BACKEND_DIR,
    "data": DATA_DIR,
    "cache": CACHE_DIR,
    "exports": EXPORT_DIR,
    "models": MODEL_DIR,
    "env": ENV_FILE,
    "api_prefix": API_PREFIX,
    "frontend_url": FRONTEND_URL,
    "host": HOST,
    "port": PORT,
    "debug": DEBUG,
    "github_graphql": GITHUB_GRAPHQL_URL,
    "default_ai_provider": DEFAULT_AI_PROVIDER,
    "default_model": DEFAULT_MODEL,
}


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

__all__ = [
    "PROJECT_ROOT",
    "BACKEND_DIR",
    "DATA_DIR",
    "CACHE_DIR",
    "EXPORT_DIR",
    "MODEL_DIR",
    "ENV_FILE",
    "DIRECTORIES",
    "GITHUB_GRAPHQL_URL",
    "GITHUB_TOKEN",
    "HF_TOKEN",
    "GITHUB_HEADERS",
    "HF_HEADERS",
    "API_PREFIX",
    "HOST",
    "PORT",
    "DEBUG",
    "FRONTEND_URL",
    "DEFAULT_AI_PROVIDER",
    "DEFAULT_MODEL",
    "CONFIG",
    "validate_environment",
]