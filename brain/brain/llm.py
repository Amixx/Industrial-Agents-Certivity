"""One interface for every LLM call, with a disk cache so reruns cost nothing.

Providers (selected by the caller; a key alone never enables a paid provider):
  * anthropic: the official SDK; models from BRAIN_MODEL_STRONG / BRAIN_MODEL_BULK
    (defaults claude-opus-5-5 / claude-sonnet-5-5). Requests opt into server-side refusal
    fallbacks.
  * openai: the OpenAI API with OPENAI_API_KEY (or OPENAI_KEY); models from BRAIN_OPENAI_STRONG /
    BRAIN_OPENAI_BULK (defaults gpt-5.5 / gpt-5.4-mini).
  * claude-cli: `claude -p` on the logged-in Claude subscription (no API key); models from
    BRAIN_CLAUDE_CLI_STRONG / BRAIN_CLAUDE_CLI_BULK (defaults claude-opus-5-5 /
    claude-sonnet-5-5), at most BRAIN_CLAUDE_CLI_WORKERS (default 5) processes at once. Text only.
  * local: any OpenAI-compatible server (Ollama, LM Studio, mlx_lm.server) at BRAIN_LOCAL_URL,
    model BRAIN_LOCAL_MODEL. This is the "runs on the engineer's laptop" mode.
  * none: no model; callers fall back to their deterministic path.

Keys can live in brain/.env (gitignored): ANTHROPIC_API_KEY=..., OPENAI_KEY=...
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .paths import CACHE, PROJECT

Tier = Literal["strong", "bulk"]

TIMEOUT = float(os.environ.get("BRAIN_LLM_TIMEOUT", "180"))  # seconds per request
RETRIES = 3  # SDK retries with backoff on timeouts, rate limits and 5xx


# USD per million tokens: input, output, cache read. Models not listed are reported as unpriced.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-fable-5-1": (10.00, 50.00, 0.25),
}


@dataclass
class Usage:
    """LLM calls and spend of this process. `cold_cost_usd` adds what the cached answers cost
    when they were first made, so runs with and without a warm cache compare."""

    calls: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cold_cost_usd: float = 0.0
    unpriced_calls: int = 0


_usage = Usage()
_usage_lock = threading.Lock()


def usage() -> dict[str, Any]:
    with _usage_lock:
        return asdict(_usage)


def usage_since(start: dict[str, Any]) -> dict[str, Any]:
    now = usage()
    return {k: round(now[k] - start[k], 4) for k in now}


def price(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0) -> float | None:
    if model not in PRICES:
        return None
    per_in, per_out, per_read = PRICES[model]
    return (input_tokens * per_in + output_tokens * per_out + cache_read * per_read) / 1e6


def record(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read: int = 0,
    cost: float | None = None,
) -> float | None:
    """Count one model call; `cost` overrides the price table (a provider that reports it).
    `input_tokens` excludes the `cache_read` tokens."""
    if cost is None:
        cost = price(model, input_tokens, output_tokens, cache_read)
    input_tokens += cache_read
    with _usage_lock:
        _usage.calls += 1
        _usage.input_tokens += input_tokens
        _usage.output_tokens += output_tokens
        if cost is None:
            _usage.unpriced_calls += 1
        else:
            _usage.cost_usd += cost
            _usage.cold_cost_usd += cost
    return cost


def _record_hit(meta: Path) -> None:
    cost = json.loads(meta.read_text()).get("cost_usd") if meta.exists() else None
    with _usage_lock:
        _usage.cache_hits += 1
        if cost is not None:
            _usage.cold_cost_usd += cost


_local = threading.local()
_provider = "none"


def _load_dotenv(path: Path = PROJECT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv()

CLI_WORKERS = int(os.environ.get("BRAIN_CLAUDE_CLI_WORKERS", "5"))
# Each claude-cli call is a process; this caps them across every thread pool in the process.
_CLI_SLOTS = threading.BoundedSemaphore(CLI_WORKERS)


def use(route: str) -> None:
    """Select the provider for this process; callers must choose it explicitly."""
    global _provider
    if route == "api":
        _provider = "anthropic"
    elif route in {"anthropic", "claude-cli", "openai", "codex-cli", "local", "none"}:
        _provider = route
    else:
        raise ValueError(f"unknown LLM route {route!r}; expected api or claude-cli")


def provider() -> str:
    return _provider


def _openai_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")


def available() -> bool:
    return provider() != "none"


def local_reasoning() -> str:
    """Local models answer without a thinking phase; BRAIN_LOCAL_REASONING=low|high turns it on."""
    return os.environ.get("BRAIN_LOCAL_REASONING", "none")


def reads_images() -> bool:
    """Local models are treated as text-only unless BRAIN_LOCAL_VISION=1; claude-cli is
    text-only."""
    if provider() == "claude-cli":
        return False
    return provider() != "local" or os.environ.get("BRAIN_LOCAL_VISION") == "1"


def batching(cloud_batch: int, local_batch: int, cloud_workers: int) -> tuple[int, int]:
    """(batch size, workers). A local server answers one request at a time within a 16k
    context (OLLAMA_CONTEXT_LENGTH), so it gets small batches and no parallel requests that
    would queue past the timeout. claude-cli runs at most CLI_WORKERS processes."""
    if provider() == "local":
        return int(os.environ.get("BRAIN_LOCAL_BATCH", local_batch)), 1
    if provider() == "claude-cli":
        return cloud_batch, min(cloud_workers, CLI_WORKERS)
    return cloud_batch, cloud_workers


def model_for(tier: Tier) -> str:
    if provider() == "local":
        return os.environ.get("BRAIN_LOCAL_MODEL", "qwen3:14b")
    if provider() == "openai":
        if tier == "strong":
            return os.environ.get("BRAIN_OPENAI_STRONG", "gpt-5.5")
        return os.environ.get("BRAIN_OPENAI_BULK", "gpt-5.4-mini")
    if provider() == "claude-cli":
        if tier == "strong":
            return os.environ.get("BRAIN_CLAUDE_CLI_STRONG", "claude-opus-5-5")
        return os.environ.get("BRAIN_CLAUDE_CLI_BULK", "claude-sonnet-5-5")
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
        raise RuntimeError("no LLM provider selected; pass --llm api or --llm claude-cli")
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
        payload["reasoning"] = local_reasoning()
        payload["temperature"] = "0"  # earlier local answers were sampled at temperature 1
    cached = _cache_path(payload)
    if cached.exists():
        try:
            result: dict[str, Any] = json.loads(cached.read_text())
            if isinstance(result, dict):
                _record_hit(cached.with_suffix(".usage.json"))
                return result
        except json.JSONDecodeError:
            pass  # a corrupt entry is recomputed and overwritten
    _local.cost = None
    if prov == "anthropic":
        result = _anthropic(model, system, content, schema, effort, max_tokens)
    elif prov == "claude-cli":
        result = _claude_cli(model, system, content, schema, effort)
    elif prov in ("openai", "local"):
        result = _openai_compatible(prov, model, system, content, schema, effort, max_tokens)
    else:
        raise RuntimeError(f"unknown LLM provider {prov!r}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(cached.with_suffix(".usage.json"), {"cost_usd": getattr(_local, "cost", None)})
    write_atomic(cached, result)
    return result


def _close_object_schemas(schema: dict[str, Any]) -> dict[str, Any]:
    """Anthropic structured output requires every object schema to be closed."""
    schema = copy.deepcopy(schema)

    def visit(node: Any) -> None:
        if not isinstance(node, dict):
            if isinstance(node, list):
                for child in node:
                    visit(child)
            return
        if node.get("type") == "object":
            node["additionalProperties"] = False
        for value in node.values():
            visit(value)

    visit(schema)
    return schema


def write_atomic(path: Path, data: Any) -> None:
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
) -> dict[str, Any]:
    import anthropic

    schema = _close_object_schemas(schema)
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
    u = response.usage
    _local.cost = record(
        model,
        u.input_tokens + (u.cache_creation_input_tokens or 0),
        u.output_tokens,
        u.cache_read_input_tokens or 0,
    )
    text = next(b.text for b in response.content if b.type == "text")
    parsed: dict[str, Any] = json.loads(text)
    return parsed


def _claude_cli(
    model: str,
    system: str,
    content: str | list[dict[str, Any]],
    schema: dict[str, Any],
    effort: str,
) -> dict[str, Any]:
    from . import claude_cli

    if isinstance(content, list):
        if any(block["type"] != "text" for block in content):
            raise ValueError("claude-cli takes text only; check llm.reads_images() first")
        prompt = "\n\n".join(block["text"] for block in content)
    else:
        prompt = content

    def on_usage(u: dict[str, Any], cost: float | None) -> None:
        _local.cost = record(
            model,
            u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
            u.get("output_tokens", 0),
            u.get("cache_read_input_tokens", 0),
            cost=cost,
        )

    with _CLI_SLOTS:
        return claude_cli.complete_json(
            system, prompt, schema, model=model, effort=effort, on_usage=on_usage
        )


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
        request["reasoning_effort"] = local_reasoning()
        request["temperature"] = 0  # Ollama's MLX tags default to temperature 1
    try:
        response = client.chat.completions.create(**request)
    except Exception as e:
        # Ollama's MLX runner (qwen3.5, gemma4) rejects constrained decoding with
        # "structured output is unavailable"; ask for JSON in the prompt instead.
        if prov != "local" or "structured output" not in str(e):
            raise
        return _prompted_json(client, request, schema)
    _record_openai(model, response)
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError(f"{model} hit the token limit")
    if choice.message.refusal:
        raise RuntimeError(f"model refused: {choice.message.refusal}")
    parsed: dict[str, Any] = json.loads(choice.message.content or "{}")
    return parsed


def _record_openai(model: str, response: Any) -> None:
    u = response.usage
    _local.cost = record(model, u.prompt_tokens if u else 0, u.completion_tokens if u else 0)


def _extract_json(text: str, schema: dict[str, Any] | None = None) -> Any:
    """The first JSON value in a reply that may wrap it in a code fence, prose or a second
    object. A bare array (Qwen sometimes drops the wrapper) is wrapped when the schema is an
    object with a single array property."""
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        raise ValueError("no JSON object in the reply")
    obj, _ = json.JSONDecoder().raw_decode(text[min(starts) :])
    props = (schema or {}).get("properties", {})
    arrays = [k for k, v in props.items() if v.get("type") == "array"]
    if isinstance(obj, list) and len(props) == 1 and arrays:
        return {arrays[0]: obj}
    return obj


def _prompted_json(client: Any, request: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Unconstrained call with the schema in the system prompt; validated, one corrective retry."""
    import jsonschema

    request = dict(request)
    request.pop("response_format", None)
    messages = [dict(m) for m in request["messages"]]
    messages[0]["content"] += (
        "\n\nReply with only one JSON object, no prose, that matches this JSON Schema:\n"
        + json.dumps(schema)
    )
    for attempt in range(2):
        response = client.chat.completions.create(**{**request, "messages": messages})
        _record_openai(request["model"], response)
        text = response.choices[0].message.content or ""
        try:
            parsed = _extract_json(text, schema)
            jsonschema.validate(parsed, schema)
            result: dict[str, Any] = parsed
            return result
        except (ValueError, jsonschema.ValidationError) as e:
            if attempt:
                raise RuntimeError(f"{request['model']} returned invalid JSON: {e}") from e
            messages += [
                {"role": "assistant", "content": text},
                {
                    "role": "user",
                    "content": f"That reply was not valid: {str(e)[:300]}. "
                    "Reply with the corrected JSON object only.",
                },
            ]
    raise AssertionError("unreachable")
