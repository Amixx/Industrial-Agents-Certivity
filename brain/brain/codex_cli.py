"""JSON-schema completions through the Codex CLI (`codex exec`) on the logged-in ChatGPT
subscription, with a disk cache so reruns cost nothing.

Meant for offline work (evaluation), not for the pipeline at runtime. Each call runs read-only in
an empty temporary folder and carries Codex's own agent prompt (about 18k tokens), so callers
should batch generously.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .paths import CACHE

DEFAULT_MODEL = "gpt-6.1-sol"
EFFORT = "medium"
TIMEOUT = 900  # seconds per call
ATTEMPTS = 3


def _cache_path(payload: dict[str, Any]) -> Path:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return CACHE / "codex_cli" / f"{digest}.json"


def complete_json(
    system: str, prompt: str, schema: dict[str, Any], model: str = DEFAULT_MODEL
) -> dict[str, Any]:
    """A JSON object matching `schema`. Raises RuntimeError after ATTEMPTS failed calls."""
    payload = {"system": system, "prompt": prompt, "schema": schema, "model": model, "e": EFFORT}
    cached = _cache_path(payload)
    if cached.exists():
        result: dict[str, Any] = json.loads(cached.read_text())
        return result
    error = ""
    for _ in range(ATTEMPTS):
        with tempfile.TemporaryDirectory() as tmp:
            schema_file, answer = Path(tmp) / "schema.json", Path(tmp) / "answer.json"
            schema_file.write_text(json.dumps(schema))
            cmd = [
                "codex", "exec",
                "-m", model,
                "-c", f"model_reasoning_effort={EFFORT}",
                "--skip-git-repo-check",
                "--ephemeral",
                "-s", "read-only",
                "-C", tmp,
                "--output-schema", str(schema_file),
                "-o", str(answer),
                f"{system}\n\n{prompt}",
            ]  # fmt: skip
            done = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT
            )
            if done.returncode != 0 or not answer.exists():
                error = done.stderr[-300:]
                continue
            try:
                result = json.loads(answer.read_text())
            except json.JSONDecodeError:
                error = f"unparseable answer: {answer.read_text()[:200]!r}"
                continue
        cached.parent.mkdir(parents=True, exist_ok=True)
        part = cached.with_suffix(f".{os.getpid()}.tmp")
        part.write_text(json.dumps(result))
        part.replace(cached)
        return result
    raise RuntimeError(f"codex exec failed {ATTEMPTS} times: {error}")
