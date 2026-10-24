"""One interface for every LLM call, with a disk cache so reruns cost nothing.

Providers (env BRAIN_LLM, default none; a key alone never enables a paid provider):
  * anthropic: the official SDK; models from BRAIN_MODEL_STRONG / BRAIN_MODEL_BULK
    (defaults claude-opus-5-5 / claude-sonnet-5-5). Requests opt into server-side refusal
    fallbacks.
  * openai: the OpenAI API with OPENAI_API_KEY (or OPENAI_KEY); models from BRAIN_OPENAI_STRONG /
    BRAIN_OPENAI_BULK (defaults gpt-5.5 / gpt-5.4-mini).
  * local: any OpenAI-compatible server (Ollama, LM Studio, mlx_lm.server) at BRAIN_LOCAL_URL,
    model BRAIN_LOCAL_MODEL. This is the "runs on the engineer's laptop" mode.
  * none: no model; callers fall back to their deterministic path.

Keys can live in brain/.env (gitignored): ANTHROPIC_API_KEY=..., OPENAI_KEY=..., BRAIN_LLM=...
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any, Literal

from .paths import CACHE, PROJECT

Tier = Literal["strong", "bulk"]

TIMEOUT = float(os.environ.get("BRAIN_LLM_TIMEOUT", "180"))  # seconds per request
RETRIES = 3  # SDK retries with backoff on timeouts, rate limits and 5xx


def _load_dotenv(path: Path = PROJECT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()


def provider() -> str:
    explicit = os.environ.get("BRAIN_LLM")
    if explicit:
        return explicit
    # Paid providers are opt-in: a key alone never starts spending. Set BRAIN_LLM explicitly.
    return "none"


def _openai_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")


def available() -> bool:
    return provider() != "none"


def model_for(tier: Tier) -> str:
    if provider() == "local":
        return os.environ.get("BRAIN_LOCAL_MODEL", "qwen3:14b")
    if provider() == "openai":
        if tier == "strong":
            return os.environ.get("BRAIN_OPENAI_STRONG", "gpt-5.5")
        return os.environ.get("BRAIN_OPENAI_BULK", "gpt-5.4-mini")
    if tier == "strong":
        return os.environ.get("BRAIN_MODEL_STRONG", "claude-opus-5-5")
    return os.environ.get("BRAIN_MODEL_BULK", "claude-sonnet-5-5")


def _cache_path(payload: dict[str, Any]) -> Path:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return CACHE / "llm" / f"{digest}.json"


def image_block(path: Path) -> dict[str, Any]:
    media = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}}


def complete_json(
    system: str,
    content: str | list[dict[str, Any]],
    schema: dict[str, Any],
    *,
    tier: Tier = "bulk",
    effort: str = "medium",
    max_tokens: int = 16000,
) -> dict[str, Any]:
    """A JSON object matching `schema`. Raises RuntimeError when no provider is configured."""
    prov = provider()
    if prov == "none":
        raise RuntimeError("no LLM: set ANTHROPIC_API_KEY, OPENAI_KEY or BRAIN_LLM=local")
    model = model_for(tier)
    payload = {
        "provider": prov,
        "model": model,
        "system": system,
        "content": content,
        "schema": schema,
        "effort": effort,
    }
    cached = _cache_path(payload)
    if cached.exists():
        try:
            result: dict[str, Any] = json.loads(cached.read_text())
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass  # a corrupt entry is recomputed and overwritten
    if prov == "anthropic":
        result = _anthropic(model, system, content, schema, effort, max_tokens)
    elif prov in ("openai", "local"):
        result = _openai_compatible(prov, model, system, content, schema, effort, max_tokens)
    else:
        raise RuntimeError(f"unknown BRAIN_LLM={prov}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    tmp = cached.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(result))
    tmp.replace(cached)  # atomic, so parallel workers never read a half-written file
    return result


def _anthropic(
    model: str,
    system: str,
    content: str | list[dict[str, Any]],
    schema: dict[str, Any],
    effort: str,
    max_tokens: int,
) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(timeout=TIMEOUT, max_retries=RETRIES)
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        # Opt into server-side refusal fallbacks (routes to a fallback model on a decline).
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
    }
    response = client.beta.messages.create(**request)
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model refused: {response.stop_details}")
    text = next(b.text for b in response.content if b.type == "text")
    parsed: dict[str, Any] = json.loads(text)
    return parsed


def _openai_compatible(
    prov: str,
    model: str,
    system: str,
    content: str | list[dict[str, Any]],
    schema: dict[str, Any],
    effort: str,
    max_tokens: int,
) -> dict[str, Any]:
    from openai import OpenAI

    if prov == "openai":
        client = OpenAI(api_key=_openai_key(), timeout=TIMEOUT, max_retries=RETRIES)
    else:
        client = OpenAI(
            base_url=os.environ.get("BRAIN_LOCAL_URL", "http://localhost:11434/v1"),
            api_key=os.environ.get("BRAIN_LOCAL_KEY", "local"),
            timeout=TIMEOUT,
            max_retries=RETRIES,
        )
    if isinstance(content, list):  # Anthropic-style blocks -> OpenAI-style parts
        parts: list[dict[str, Any]] = []
        for block in content:
            if block["type"] == "text":
                parts.append({"type": "text", "text": block["text"]})
            elif block["type"] == "image":
                src = block["source"]
                url = f"data:{src['media_type']};base64,{src['data']}"
                parts.append({"type": "image_url", "image_url": {"url": url}})
        user: Any = parts
    else:
        user = content
    request: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "result", "schema": schema, "strict": True},
        },
    }
    if prov == "openai":  # reasoning models: the token cap includes the reasoning tokens
        request["max_completion_tokens"] = max_tokens * 2
        request["reasoning_effort"] = effort
    else:
        request["max_tokens"] = max_tokens
    response = client.chat.completions.create(**request)
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(f"{model} hit the token limit")
    if choice.message.refusal:
        raise RuntimeError(f"model refused: {choice.message.refusal}")
    parsed: dict[str, Any] = json.loads(choice.message.content or "{}")
    return parsed
