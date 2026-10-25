"""JSON-schema completions through the Claude Code CLI (`claude -p`) on the logged-in
subscription, with a disk cache so reruns cost nothing.

Used by the model judge and by `llm` under BRAIN_LLM=claude-cli. The API key is removed from
the child's environment so calls never bill the API. Claude Code's own system prompt, tools,
settings and MCP servers are switched off, so a call carries only the prompt. Prompt caching is off
too: each call is a fresh process with its own prompt, so Claude Code's one-hour cache writes
(twice the input price) would never be read.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .paths import CACHE

DEFAULT_MODEL = "claude-sonnet-5-5"
TIMEOUT = 600  # seconds per call
ATTEMPTS = 3


def _cache_path(payload: dict[str, Any]) -> Path:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return CACHE / "claude_cli" / f"{digest}.json"


def complete_json(
    system: str,
    prompt: str,
    schema: dict[str, Any],
    model: str = DEFAULT_MODEL,
    effort: str | None = None,
    on_usage: Callable[[dict[str, Any], float | None], None] | None = None,
) -> dict[str, Any]:
    """A JSON object matching `schema`. `effort` (low to max) defaults to the CLI's own setting.
    Raises RuntimeError after ATTEMPTS failed calls."""
    key: dict[str, Any] = {"system": system, "prompt": prompt, "schema": schema, "model": model}
    if effort is not None:
        key["effort"] = effort
    cached = _cache_path(key)
    if cached.exists():
        result: dict[str, Any] = json.loads(cached.read_text())
        return result
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["DISABLE_PROMPT_CACHING"] = "1"
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--system-prompt", system,
        "--tools", "",
        "--strict-mcp-config",
        "--setting-sources", "",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--output-format", "json",
        "--json-schema", json.dumps(schema),
    ]  # fmt: skip
    if effort is not None:
        cmd += ["--effort", effort]
    error = ""
    for _ in range(ATTEMPTS):
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, env=env)
        out = done.stdout
        try:
            reply = json.loads(out[out.find("{") : out.rfind("}") + 1])
        except json.JSONDecodeError:
            error = f"unparseable output: {out[:200]!r} {done.stderr[:200]!r}"
            continue
        if reply.get("is_error"):
            error = str(reply.get("result"))[:300]
            continue
        result = reply.get("structured_output") or json.loads(reply["result"])
        if on_usage is not None:
            on_usage(reply.get("usage") or {}, reply.get("total_cost_usd"))
        cached.parent.mkdir(parents=True, exist_ok=True)
        tmp = cached.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(result))
        tmp.replace(cached)
        return result
    raise RuntimeError(f"claude -p failed {ATTEMPTS} times: {error}")
