"""
LLM client factory.

Centralized construction of OpenAI and Anthropic SDK clients with opt-in
routing through a LiteLLM gateway. When LLM_GATEWAY_BASE_URL and
LLM_GATEWAY_API_KEY are BOTH set, clients are pointed at the gateway;
otherwise clients are constructed with SDK defaults (no behavior change).

Gateway URL contract:
- OpenAI SDK receives LLM_GATEWAY_BASE_URL verbatim (include the /v1 suffix,
  e.g. http://localhost:18400/v1).
- Anthropic SDK receives LLM_GATEWAY_BASE_URL with a trailing /v1 stripped
  (the anthropic SDK appends /v1/messages itself, e.g. http://localhost:18400).
"""

from __future__ import annotations

import os

import anthropic
import openai


def _gateway_config() -> tuple[str | None, str | None]:
    """Return (base_url, api_key) when the gateway pair is fully set."""
    base_url = os.getenv("LLM_GATEWAY_BASE_URL")
    api_key = os.getenv("LLM_GATEWAY_API_KEY")
    if base_url and api_key:
        return base_url, api_key
    return None, None


def _anthropic_base_url(base_url: str) -> str:
    """Strip a trailing /v1 so the anthropic SDK can append /v1/messages."""
    stripped = base_url.rstrip("/")
    if stripped.endswith("/v1"):
        stripped = stripped[: -len("/v1")]
    return stripped


def create_openai_client() -> openai.OpenAI:
    """Construct an OpenAI SDK client, gateway-routed when the env pair is set."""
    base_url, api_key = _gateway_config()
    if base_url and api_key:
        return openai.OpenAI(base_url=base_url, api_key=api_key)
    return openai.OpenAI()


def create_anthropic_client() -> anthropic.Anthropic:
    """Construct an Anthropic SDK client, gateway-routed when the env pair is set."""
    base_url, api_key = _gateway_config()
    if base_url and api_key:
        return anthropic.Anthropic(
            base_url=_anthropic_base_url(base_url), api_key=api_key
        )
    return anthropic.Anthropic()
