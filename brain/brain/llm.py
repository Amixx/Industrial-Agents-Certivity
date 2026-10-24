"""One interface for every LLM call, with a disk cache so reruns cost nothing.

Providers (env BRAIN_LLM, default none; a key alone never enables a paid provider):
  * anthropic: the official SDK; models from BRAIN_MODEL_STRONG / BRAIN_MODEL_BULK
    (defaults claude-opus-5-5 / claude-sonnet-5-5). BRAIN_MODEL sets both tiers at once.
    Each accepts an id or an alias: opus, sonnet, fable, haiku. Requests stream (Fable turns
    can run for minutes) and opt into server-side refusal fallbacks.
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

CLAUDE = {
    "opus": "claude-opus-5-5",
    "sonnet": "claude-sonnet-5-5",
    "fable": "claude-fable-5-1",
    "haiku": "claude-haiku-5-5",
}
# USD per million tokens: input, output, cache read. A 5-minute cache write is 1.25x input.
PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20),
    "claude-fable-5-1": (10.0, 50.0, 0.25),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}


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


def local_reasoning(effort: str) -> str:
    """Local models think only on high-effort calls (regulation review).

    BRAIN_LOCAL_REASONING overrides this for every call.
    """
    return os.environ.get("BRAIN_LOCAL_REASONING") or ("high" if effort == "high" else "none")


def reads_images() -> bool:
    """Local models are treated as text-only unless BRAIN_LOCAL_VISION=1."""
    return provider() != "local" or os.environ.get("BRAIN_LOCAL_VISION") == "1"


def model_for(tier: Tier) -> str:
    if provider() == "local":
        return os.environ.get("BRAIN_LOCAL_MODEL", "qwen3:14b")
    if provider() == "openai":
        if tier == "strong":
            return os.environ.get("BRAIN_OPENAI_STRONG", "gpt-5.5")
        return os.environ.get("BRAIN_OPENAI_BULK", "gpt-5.4-mini")
    both = os.environ.get("BRAIN_MODEL")
    if tier == "strong":
        name = os.environ.get("BRAIN_MODEL_STRONG") or both or "opus"
    else:
        name = os.environ.get("BRAIN_MODEL_BULK") or both or "sonnet"
    return CLAUDE.get(name, name)


Usage = dict[str, dict[str, int]]  # model -> calls and token counts

_usage: dict[str, Usage] = {"paid": {}, "cached": {}}
_usage_lock = threading.Lock()


def _add(kind: str, model: str, counts: dict[str, int]) -> None:
    with _usage_lock:
        total = _usage[kind].setdefault(model, dict.fromkeys(counts, 0))
        for key, value in counts.items():
            total[key] = total.get(key, 0) + value


def _record(model: str, usage: Any) -> dict[str, int]:
    counts = {
        "calls": 1,
        "input": usage.input_tokens or 0,
        "output": usage.output_tokens or 0,
        "cache_read": usage.cache_read_input_tokens or 0,
        "cache_write": usage.cache_creation_input_tokens or 0,
    }
    _add("paid", model, counts)
    return counts


def usage(cached: bool = False) -> Usage:
    """Tokens per model for the paid calls made in this process, or (cached=True) the original
    usage of the responses this process read from the disk cache, which cost nothing now."""
    with _usage_lock:
        return {model: dict(c) for model, c in _usage["cached" if cached else "paid"].items()}


def cost(counts: dict[str, dict[str, int]] | None = None) -> float | None:
    """USD for `counts` (default: this process so far); None if a model has no price."""
    total = 0.0
    for model, c in (usage() if counts is None else counts).items():
        if model not in PRICES:
            return None
        inp, out, read = PRICES[model]
        total += (
            c["input"] * inp
            + c["cache_write"] * inp * 1.25
            + c["cache_read"] * read
            + c["output"] * out
        ) / 1e6
    return total


def _describe(counts: Usage) -> str:
    parts = [
        f"{model} {c['calls']} calls, {c['input'] + c['cache_read'] + c['cache_write']:,} in"
        f" / {c['output']:,} out"
        for model, c in counts.items()
    ]
    usd = cost(counts)
    return "; ".join(parts) + (f"; ${usd:.2f}" if usd is not None else "")


def usage_line() -> str:
    paid, cached = usage(), usage(cached=True)
    if not paid and not cached:
        return "LLM usage: none (deterministic)"
    line = "LLM usage: " + (_describe(paid) if paid else "no paid calls")
    if cached:
        line += f". From cache (paid on an earlier run): {_describe(cached)}"
    return line


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
        raise RuntimeError("no LLM: set BRAIN_LLM=anthropic, openai or local")
    model = model_for(tier)
    payload = {
        "provider": prov,
        "model": model,
        "system": system,
        "content": content,
        "schema": schema,
        "effort": effort,
    }
    if prov == "local":
        payload["reasoning"] = local_reasoning(effort)
    cached = _cache_path(payload)
    spent = cached.with_suffix(".usage.json")  # the tokens the cached response cost
    if cached.exists():
        try:
            result: dict[str, Any] = json.loads(cached.read_text())
            if isinstance(result, dict):
                if spent.exists():
                    _add("cached", model, json.loads(spent.read_text()))
                return result
        except json.JSONDecodeError:
            pass  # a corrupt entry is recomputed and overwritten
    counts: dict[str, int] | None = None
    if prov == "anthropic":
        result, counts = _anthropic(model, system, content, schema, effort, max_tokens)
    elif prov in ("openai", "local"):
        result = _openai_compatible(prov, model, system, content, schema, effort, max_tokens)
    else:
        raise RuntimeError(f"unknown BRAIN_LLM={prov}")
    if counts is not None:
        _write_atomic(spent, counts)
    _write_atomic(cached, result)
    return result


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)  # atomic, so parallel workers never read a half-written file


def _anthropic(
    model: str,
    system: str,
    content: str | list[dict[str, Any]],
    schema: dict[str, Any],
    effort: str,
    max_tokens: int,
) -> tuple[dict[str, Any], dict[str, int]]:
    import anthropic

    client = anthropic.Anthropic(timeout=TIMEOUT, max_retries=RETRIES)
    request: dict[str, Any] = {
        "model": model,
        # Thinking is always on for Opus 5.5 and Fable 5.1 and counts toward the cap.
        "max_tokens": max_tokens * 2,
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        # Opt into server-side refusal fallbacks (routes to a fallback model on a decline).
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
    }
    with client.beta.messages.stream(**request) as stream:
        response = stream.get_final_message()
    counts = _record(model, response.usage)
    if response.stop_reason == "refusal":
        raise RuntimeError(f"model refused: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError(f"{model} hit the token limit")
    text = next(b.text for b in response.content if b.type == "text")
    parsed: dict[str, Any] = json.loads(text)
    return parsed, counts


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
        request["reasoning_effort"] = local_reasoning(effort)
    response = client.chat.completions.create(**request)
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(f"{model} hit the token limit")
    if choice.message.refusal:
        raise RuntimeError(f"model refused: {choice.message.refusal}")
    parsed: dict[str, Any] = json.loads(choice.message.content or "{}")
    return parsed
