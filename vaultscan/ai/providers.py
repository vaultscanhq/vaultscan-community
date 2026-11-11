"""Model providers for the AI reviewer.

Only the standard library is used so the scanner stays a small install.
Configuration comes from environment variables:

    VAULTSCAN_AI_PROVIDER   anthropic | openai | ollama
    VAULTSCAN_AI_MODEL      model name (required)
    VAULTSCAN_AI_BASE_URL   override the API endpoint (optional)
    VAULTSCAN_AI_API_KEY    falls back to ANTHROPIC_API_KEY / OPENAI_API_KEY

`ollama` (or any OpenAI-compatible server on your own machine) keeps the
whole review local, which fits the privacy-first goal of the project.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Mapping, Optional

TIMEOUT_SECONDS = 60


class ProviderError(RuntimeError):
    pass


def _post(url: str, headers: Mapping[str, str], payload: dict) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", **headers}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"model API returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ProviderError(f"could not reach the model API: {exc}") from exc


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str, api_key: str, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")

    def complete(self, system: str, prompt: str) -> str:
        data = _post(
            f"{self.base_url}/v1/messages",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            {"model": self.model, "max_tokens": 2000, "system": system,
             "messages": [{"role": "user", "content": prompt}]},
        )
        try:
            return "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise ProviderError("unexpected response shape from the Anthropic API") from exc


class OpenAICompatibleProvider:
    """Works with OpenAI, Ollama, vLLM, LM Studio and similar servers."""

    name = "openai"

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    def complete(self, system: str, prompt: str) -> str:
        headers = {"authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post(
            f"{self.base_url}/chat/completions", headers,
            {"model": self.model, "temperature": 0,
             "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("unexpected response shape from the chat completions API") from exc


def provider_from_env(env: Optional[Mapping[str, str]] = None):
    """Build a provider from the environment, or return None if AI is not configured."""
    env = os.environ if env is None else env
    kind = env.get("VAULTSCAN_AI_PROVIDER", "").strip().lower()
    if not kind:
        return None
    model = env.get("VAULTSCAN_AI_MODEL", "").strip()
    if not model:
        raise ProviderError("VAULTSCAN_AI_MODEL must be set when VAULTSCAN_AI_PROVIDER is set")
    base_url = env.get("VAULTSCAN_AI_BASE_URL") or None
    key = env.get("VAULTSCAN_AI_API_KEY") or None
    if kind == "anthropic":
        key = key or env.get("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("set ANTHROPIC_API_KEY or VAULTSCAN_AI_API_KEY to use the anthropic provider")
        return AnthropicProvider(model, key, base_url)
    if kind == "openai":
        key = key or env.get("OPENAI_API_KEY")
        if not key and not base_url:
            raise ProviderError("set OPENAI_API_KEY or VAULTSCAN_AI_API_KEY to use the openai provider")
        return OpenAICompatibleProvider(model, key, base_url)
    if kind == "ollama":
        return OpenAICompatibleProvider(model, key, base_url or "http://localhost:11434/v1")
    raise ProviderError(f"unknown VAULTSCAN_AI_PROVIDER: {kind!r} (use anthropic, openai or ollama)")
