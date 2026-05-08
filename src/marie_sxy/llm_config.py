"""Map unified ``MARIE_SXY_*`` settings onto LiteLLM provider environment variables."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"

# LiteLLM provider slug -> env var that holds the API key for that route.
# https://docs.litellm.ai/docs/providers
_PROVIDER_API_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "azure": "AZURE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "google": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "cohere": "COHERE_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "together_ai": "TOGETHER_API_KEY",
    "together": "TOGETHER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "xai": "XAI_API_KEY",
    "fireworks_ai": "FIREWORKS_AI_API_KEY",
    "fireworks": "FIREWORKS_AI_API_KEY",
    "nvidia_nim": "NVIDIA_NIM_API_KEY",
}


def infer_litellm_provider(model: str) -> str:
    """Infer LiteLLM provider slug from ``MARIE_SXY_MODEL``."""
    m = model.strip().lower()
    if "/" in m:
        return m.split("/", 1)[0].strip()
    if any(
        m.startswith(p)
        for p in (
            "gpt-",
            "o1",
            "o3",
            "o4",
            "chatgpt-",
            "davinci",
            "text-embedding",
            "text-davinci",
            "ft:",
        )
    ):
        return "openai"
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gemini-"):
        return "gemini"
    return "openai"


def api_key_env_for_provider(provider: str) -> str:
    """Return the ``os.environ`` key LiteLLM expects for this provider."""
    p = provider.strip().lower()
    if p in _PROVIDER_API_ENV:
        return _PROVIDER_API_ENV[p]
    clean = p.upper().replace("-", "_")
    generic = f"{clean}_API_KEY"
    logger.debug("Using generic API key env %s for provider %s", generic, provider)
    return generic


def apply_marie_sxy_unified_credentials() -> None:
    """If ``MARIE_SXY_API_KEY`` is set, copy it to the provider-specific env var.

    Users only maintain ``MARIE_SXY_API_KEY`` + ``MARIE_SXY_MODEL``; switching models
    switches which provider env gets the key (LiteLLM reads provider vars).

    Does nothing when ``MARIE_SXY_API_KEY`` is unset (legacy per-provider keys still work).
    """
    unified = os.environ.get("MARIE_SXY_API_KEY")
    if unified is None or not str(unified).strip():
        return

    model = os.environ.get("MARIE_SXY_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    provider = infer_litellm_provider(model)
    target = api_key_env_for_provider(provider)
    os.environ[target] = unified.strip()
