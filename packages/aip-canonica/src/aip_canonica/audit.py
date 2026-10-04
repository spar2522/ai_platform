"""Audit and connectivity tracking for Canonica AI and network requests."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("aip_canonica.audit")


def get_ai_connectivity_info(ai: Any) -> dict[str, Any]:
    """Inspect an AI instance or configuration to determine provider and external network usage."""
    if ai is None:
        return {
            "ai_used": False,
            "provider": None,
            "model": None,
            "endpoint": None,
            "is_external_network": False,
            "connectivity_type": "offline",
            "summary": "100% Deterministic (Offline / Zero Network)",
        }

    config = getattr(ai, "config", None)
    provider_name = str(getattr(config, "provider", "unknown") or "unknown").lower()
    model = getattr(config, "model", None)
    base_url = getattr(config, "base_url", None)

    if "dummy" in provider_name:
        return {
            "ai_used": True,
            "provider": "dummy",
            "model": model or "mock-model",
            "endpoint": "in-memory",
            "is_external_network": False,
            "connectivity_type": "offline_mock",
            "summary": "Offline Mock (In-memory, 0 network requests)",
        }

    if "ollama" in provider_name or "local" in provider_name:
        endpoint = base_url or "http://localhost:11434"
        return {
            "ai_used": True,
            "provider": "ollama",
            "model": model or "local-default",
            "endpoint": endpoint,
            "is_external_network": False,
            "connectivity_type": "localhost_api",
            "summary": f"LOCALHOST ONLY ({endpoint} - Zero external internet traffic)",
        }

    if "gemini" in provider_name:
        endpoint = base_url or "https://generativelanguage.googleapis.com"
        return {
            "ai_used": True,
            "provider": "gemini",
            "model": model or "gemini-3.5-flash",
            "endpoint": endpoint,
            "is_external_network": True,
            "connectivity_type": "cloud_internet",
            "summary": f"EXTERNAL INTERNET (Google Gemini API via {endpoint})",
        }

    if "openai" in provider_name:
        endpoint = base_url or "https://api.openai.com/v1"
        return {
            "ai_used": True,
            "provider": "openai",
            "model": model or "gpt-4o",
            "endpoint": endpoint,
            "is_external_network": True,
            "connectivity_type": "cloud_internet",
            "summary": f"EXTERNAL INTERNET (OpenAI API via {endpoint})",
        }

    if "anthropic" in provider_name:
        endpoint = base_url or "https://api.anthropic.com"
        return {
            "ai_used": True,
            "provider": "anthropic",
            "model": model or "claude-3-7-sonnet",
            "endpoint": endpoint,
            "is_external_network": True,
            "connectivity_type": "cloud_internet",
            "summary": f"EXTERNAL INTERNET (Anthropic API via {endpoint})",
        }

    # Generic fallback
    is_external = True
    if base_url and ("localhost" in base_url or "127.0.0.1" in base_url):
        is_external = False

    return {
        "ai_used": True,
        "provider": provider_name,
        "model": model,
        "endpoint": base_url or "cloud-api",
        "is_external_network": is_external,
        "connectivity_type": "cloud_internet" if is_external else "localhost_api",
        "summary": "EXTERNAL INTERNET" if is_external else "LOCALHOST ONLY",
    }


def log_api_notice(
    purpose: str,
    ai: Any,
    *,
    document_name: str = "",
    extra_details: str = "",
) -> None:
    """Print and log an explicit, prominent notice whenever an AI or network API call is initiated."""
    info = get_ai_connectivity_info(ai)
    divider = "=" * 70

    msg = (
        f"\n{divider}\n"
        f"[Canonica][API Notice] Network / API Request Initiated\n"
        f"  • Purpose: {purpose}\n"
        f"  • Connectivity: {info['summary']}\n"
        f"  • Provider: {info['provider']}\n"
        f"  • Model: {info['model'] or 'default'}\n"
        f"  • Endpoint: {info['endpoint']}\n"
    )
    if document_name:
        msg += f"  • Target Document: {document_name}\n"
    if extra_details:
        msg += f"  • Note: {extra_details}\n"
    msg += f"{divider}\n"

    # Log to both standard logger and print so it is unmissable
    logger.info(msg)
    print(msg, flush=True)


def log_token_usage(response: Any, *, title: str = "Token Usage Metrics") -> dict[str, int]:
    """Log and display token consumption for an AI API response."""
    usage = getattr(response, "usage", None)
    if not usage:
        return {}

    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    total_tokens = getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)

    divider = "-" * 70
    msg = (
        f"\n{divider}\n"
        f"[Canonica][Token Usage] {title}\n"
        f"  • Input (Prompt) Tokens:      {prompt_tokens:>8,}\n"
        f"  • Output (Completion) Tokens: {completion_tokens:>8,}\n"
        f"  • Total Tokens Utilized:      {total_tokens:>8,}\n"
        f"  • Remaining Quota Note: Gemini quotas are rolling (e.g. 1M TPM, 1.5K RPD).\n"
        f"    View your live account limits at: https://aistudio.google.com/app/plan_information\n"
        f"{divider}\n"
    )
    logger.info(msg)
    print(msg, flush=True)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }

