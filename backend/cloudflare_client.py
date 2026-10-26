"""Shared Cloudflare Workers AI client for Orzyn's LLM features."""
from __future__ import annotations

import os
from typing import Any

import requests

from backend.orzyn import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, get_active_model


class CloudflareInferenceError(RuntimeError):
    """Raised when Cloudflare Workers AI cannot complete an inference request."""


def generate_text(
    *,
    system_prompt: str,
    prompt: str,
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int = 1200,
) -> tuple[str, str, dict[str, Any]]:
    """Call Cloudflare's OpenAI-compatible Workers AI endpoint."""
    if not CLOUDFLARE_ACCOUNT_ID:
        raise CloudflareInferenceError(
            "Missing CLOUDFLARE_ACCOUNT_ID. Copy it from Cloudflare Dashboard > Workers AI."
        )
    if not CLOUDFLARE_API_TOKEN:
        raise CloudflareInferenceError(
            "Missing CLOUDFLARE_API_TOKEN. Create a Workers AI API token and add it to the backend environment."
        )

    config = get_active_model()
    model_name = model or config.model
    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/v1/chat/completions"
    )
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": config.temperature if temperature is None else temperature,
        "top_p": config.top_p if top_p is None else top_p,
    }
    timeout = max(10, int(config.timeout))
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise CloudflareInferenceError(
            f"Cloudflare Workers AI timed out after {timeout}s while using {model_name}."
        ) from exc
    except requests.RequestException as exc:
        raise CloudflareInferenceError(f"Could not reach Cloudflare Workers AI: {exc}") from exc

    try:
        data = response.json()
    except ValueError:
        data = {"raw_response": response.text[:1000]}

    if not response.ok:
        errors = data.get("errors") if isinstance(data, dict) else None
        detail = "; ".join(
            str(item.get("message", item)) if isinstance(item, dict) else str(item)
            for item in (errors or [])
        ) or str(data)[:1000]
        if response.status_code == 401 or response.status_code == 403:
            hint = " Check that the token has Workers AI Read/Write permission and matches this account."
        elif response.status_code == 429:
            hint = " Cloudflare rate or usage limits may have been reached."
        elif response.status_code >= 500:
            hint = " Cloudflare's inference service may be temporarily unavailable."
        else:
            hint = " Verify that the configured model ID is available to your account."
        raise CloudflareInferenceError(
            f"Cloudflare Workers AI returned HTTP {response.status_code} for {model_name}: {detail}.{hint}"
        )

    # The OpenAI-compatible endpoint returns choices[0].message.content.
    choices = data.get("choices", []) if isinstance(data, dict) else []
    content = None
    if choices:
        message = choices[0].get("message", {}) or {}
        content = message.get("content")
    # Be tolerant of Workers AI envelope responses if Cloudflare changes formats.
    if not content and isinstance(data, dict):
        result = data.get("result", {})
        if isinstance(result, dict):
            content = result.get("response") or result.get("output_text")

    if not isinstance(content, str) or not content.strip():
        raise CloudflareInferenceError(
            f"Cloudflare Workers AI returned no text for {model_name}. Response: {str(data)[:800]}"
        )
    return content.strip(), model_name, data
