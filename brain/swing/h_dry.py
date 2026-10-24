"""Lane H dry run: cache hits and a dollar estimate. Never calls the API.

    PYTHONPATH=. uv run python swing/h_dry.py

Run 1 is Opus relevance at blend weight 0.7 (the pipeline cut) and main's Sonnet rewrite.
Run 2 is Sonnet relevance and rewrite at weight 0.85. Run 3 is Haiku relevance at weight
0.85 and a Sonnet rewrite of the paragraphs Haiku selected. Profile and regulation choice
stay on the cached Opus answers: the three runs differ in selection, not in the product.
A g_runs-style swap of the strong model would also re-call profile and regulation review;
those keys are probed and reported separately, and they are not in the headline estimate.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain import features as F
from brain import llm, relevance, rewrite
from brain.decide import MODEL_PATH, Model
from brain.graph import build
from brain.ingest import load_all
from brain.paths import CASES
from brain.profile import build_profile
from brain.select_regs import choose

ROOT = Path(__file__).resolve().parents[2]
CASE = CASES / "dev-rear-lamp"
OUT = ROOT / "out" / "experiments" / "H-dry.json"
IMAGE = CASE / "exploded_view.png"

# List prices, $ per million tokens: input, output, cache read.
# Haiku is the rate lane G used; the run log's table does not list it.
PRICE = {
    "claude-opus-5-5": (4.0, 20.0, 0.2),
    "claude-sonnet-5-5": (2.0, 10.0, 0.2),
    "claude-haiku-5-5": (0.1, 0.5, 0.01),
}
# mix-noimage.log: the Opus strong-tier run that filled the lamp cache.
OPUS_CALLS = 115
OPUS_IN = 667_122
OPUS_OUT = 98_058
OPUS_CR = 77_770
# rear-lamp-mix.log: Sonnet rewrite of the pipeline's 267 paragraphs, main's prompt.
REWRITE_CALLS = 23
REWRITE_DOLLARS = 0.854436

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-5-5"

kind: ContextVar[str] = ContextVar("h_kind", default="other")


class DryMiss(RuntimeError):
    """A cache miss. The dry run stops this call before the SDK."""


@dataclass
class Call:
    kind: str
    model: str
    hit: bool
    system_chars: int
    user_chars: int
    image_tokens: int
    out_chars: int
    n_items: int
    system_hash: str


@dataclass
class BatchProbe:
    model: str
    hits: int = 0
    misses: int = 0
    scores: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    calls: list[Call] = field(default_factory=list)


def png_tokens(path: Path) -> int:
    """Anthropic's image token count, (width * height) / 750."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return 0
    width, height = struct.unpack(">II", data[16:24])
    return math.ceil(width * height / 750)


def content_parts(content: Any, image_tokens: int) -> tuple[int, int]:
    if isinstance(content, str):
        return len(content), 0
    text = 0
    images = 0
    for block in content:
        if block.get("type") == "text":
            text += len(str(block.get("text", "")))
        elif block.get("type") == "image":
            images += 1
    return text, image_tokens if images else 0


def install_guard(image_tokens: int) -> list[Call]:
    """Replace complete_json. A hit reads the cache. A miss raises DryMiss."""
    calls: list[Call] = []
    orig = llm.complete_json

    def blocked(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("lane H dry run blocked a network call")

    llm._anthropic = blocked  # type: ignore[attr-defined]
    llm._openai_compatible = blocked  # type: ignore[attr-defined]

    def cj(system: str, content: Any, schema: Any, *, tier: str = "bulk", **kw: Any) -> Any:
        model = llm.model_for(tier)  # type: ignore[arg-type]
        payload = {
            "provider": llm.provider(),
            "model": model,
            "system": system,
            "content": content,
            "schema": schema,
            "effort": kw.get("effort", "medium"),
        }
        path = llm._cache_path(payload)
        user_chars, img = content_parts(content, image_tokens)
        n_items = 0
        if isinstance(content, str):
            n_items = content.count('\n{"id":')
        rec = Call(
            kind=kind.get(),
            model=model,
            hit=path.exists(),
            system_chars=len(system),
            user_chars=user_chars,
            image_tokens=img,
            out_chars=len(path.read_text()) if path.exists() else 0,
            n_items=n_items,
            system_hash=hashlib.sha256(system.encode()).hexdigest()[:12],
        )
        calls.append(rec)
        if not path.exists():
            raise DryMiss(model)
        return orig(system, content, schema, tier=tier, **kw)  # type: ignore[arg-type]

    llm.complete_json = cj  # type: ignore[assignment]
    return calls


def blend(model_p: float, llm_p: float | None, weight: float) -> float:
    if llm_p is None:
        return model_p
    return float(model_p ** (1 - weight) * max(llm_p, 1e-3) ** weight)


def selected(
    paragraphs: list[Any],
    model_p: list[float],
    llm_p: dict[str, float],
    weight: float,
) -> list[Any]:
    scored = [
        (p, blend(m, llm_p.get(p.id), weight)) for p, m in zip(paragraphs, model_p, strict=True)
    ]
    keep = relevance.floor(scored, relevance.THRESHOLD)
    return [p for p, _ in scored if p.id in keep]


def probe_relevance(
    paragraphs: list[Any], graph: Any, product_json: str, model: str, batch: int
) -> BatchProbe:
    os.environ["BRAIN_MODEL_STRONG"] = model
    out = BatchProbe(model=model)
    token = kind.set("relevance")
    try:
        for i in range(0, len(paragraphs), batch):
            chunk = paragraphs[i : i + batch]
            try:
                out.scores |= relevance._batch(chunk, graph, product_json, "strong")
                out.hits += 1
            except DryMiss:
                out.misses += 1
            except Exception as e:
                out.errors.append(f"{type(e).__name__}: {e}"[:200])
                out.misses += 1
    finally:
        kind.reset(token)
    out.calls = []  # filled by the caller from the guard log
    return out


def probe_rewrite(
    paragraphs: list[Any], graph: Any, product: str, batch: int
) -> tuple[int, int, list[str]]:
    os.environ["BRAIN_MODEL_BULK"] = SONNET
    hits = misses = 0
    errors: list[str] = []
    token = kind.set("rewrite")
    try:
        for i in range(0, len(paragraphs), batch):
            chunk = paragraphs[i : i + batch]
            try:
                rewrite._batch(chunk, graph, product)
                hits += 1
            except DryMiss:
                misses += 1
            except Exception as e:
                errors.append(f"{type(e).__name__}: {e}"[:200])
                misses += 1
    finally:
        kind.reset(token)
    return hits, misses, errors


def dollars(model: str, inp: float, out: float, cache_read: float) -> float:
    pi, po, pc = PRICE[model]
    return (inp * pi + out * po + cache_read * pc) / 1e6


def prompt_tokens(c: Call, chars_per_token: float) -> tuple[float, float]:
    return c.system_chars / chars_per_token, c.user_chars / chars_per_token + c.image_tokens


def as_new(calls: list[Call], chars_per_token: float) -> dict[str, float]:
    """Token split if every call were new, output taken from the cached JSON length."""
    seen: set[str] = set()
    inp = out = cache_read = 0.0
    for c in calls:
        sys_t, user_t = prompt_tokens(c, chars_per_token)
        if c.system_hash in seen:
            cache_read += sys_t
            inp += user_t
        else:
            seen.add(c.system_hash)
            inp += sys_t + user_t
        out += c.out_chars / chars_per_token
    return {"in": inp, "out": out, "cache_read": cache_read}


def miss_bill(calls: list[Call], chars_per_token: float, out_per_item: float) -> dict[str, float]:
    """Token split for cache misses. `out_per_item` is already in output tokens."""
    seen: set[str] = set()
    inp = out = cache_read = 0.0
    for c in calls:
        if c.hit:
            continue
        sys_t, user_t = prompt_tokens(c, chars_per_token)
        if c.system_hash in seen:
            cache_read += sys_t
            inp += user_t
        else:
            seen.add(c.system_hash)
            inp += sys_t + user_t
        out += out_per_item * (c.n_items or 25)
    return {"in": inp, "out": out, "cache_read": cache_read}


def main() -> int:
    os.environ["BRAIN_LLM"] = "anthropic"
    os.environ["BRAIN_MODEL_STRONG"] = OPUS
    os.environ["BRAIN_MODEL_BULK"] = SONNET
    image_tokens = png_tokens(IMAGE) if IMAGE.exists() else 0
    calls = install_guard(image_tokens)

    spec = (CASE / "spec.md").read_text()
    token = kind.set("profile")
    try:
        profile = build_profile(spec, IMAGE if IMAGE.exists() else None, use_llm=True)
    finally:
        kind.reset(token)
    corpus = load_all("base")
    token = kind.set("regs")
    try:
        choices = choose(profile, corpus, use_llm=True)
    finally:
        kind.reset(token)
    regs = [c.regulation for c in choices if c.selected]
    sub = {r: corpus[r] for r in regs}
    graph = build(sub, set(corpus))
    paragraphs = [
        p
        for r in regs
        for p in sub[r]
        if p.number and p.label != "preamble" and not p.label.startswith("Rationale")
    ]
    ctx = F.build_context(profile, sub, graph, {c.regulation: c.probability for c in choices})
    model_p = [float(x) for x in Model.load(MODEL_PATH).predict(F.matrix(paragraphs, ctx))]
    product_json = profile.model_dump_json(
        include={"product", "vehicle_categories", "functions", "parts", "electronics"}
    )
    rel_batch, _ = llm.batching(25, 8, 12)
    rw_batch, _ = llm.batching(12, 4, 16)

    start = len(calls)
    rel = {
        name: probe_relevance(paragraphs, graph, product_json, model, rel_batch)
        for name, model in (("opus", OPUS), ("sonnet", SONNET), ("haiku", HAIKU))
    }
    # The guard log is the source of call records; slice it back onto each probe.
    rel_calls = calls[start:]
    offset = 0
    for name in ("opus", "sonnet", "haiku"):
        n = rel[name].hits + rel[name].misses
        rel[name].calls = rel_calls[offset : offset + n]
        offset += n
    os.environ["BRAIN_MODEL_STRONG"] = OPUS

    opus_scores = rel["opus"].scores
    opus_complete = rel["opus"].misses == 0 and not rel["opus"].errors
    sets: dict[str, list[Any]] = {}
    if opus_complete:
        sets["opus-w70"] = selected(paragraphs, model_p, opus_scores, 0.7)
        sets["opus-w85"] = selected(paragraphs, model_p, opus_scores, 0.85)
    for name, weight in (("sonnet", 0.85), ("haiku", 0.85)):
        probe = rel[name]
        if probe.misses == 0 and not probe.errors and len(probe.scores) >= len(paragraphs) * 0.99:
            sets[name] = selected(paragraphs, model_p, probe.scores, weight)

    rewrite_stats: dict[str, dict[str, Any]] = {}
    for name, rows in sets.items():
        before = len(calls)
        hits, misses, errors = probe_rewrite(rows, graph, profile.product, rw_batch)
        rewrite_stats[name] = {
            "paragraphs": len(rows),
            "hits": hits,
            "misses": misses,
            "errors": errors,
            "calls": calls[before:],
        }

    # Side probe: profile and regulation review if the strong model itself changes.
    side: dict[str, dict[str, Any]] = {}
    for model in (SONNET, HAIKU):
        os.environ["BRAIN_MODEL_STRONG"] = model
        before = len(calls)
        token = kind.set("profile")
        try:
            build_profile(spec, IMAGE if IMAGE.exists() else None, use_llm=True)
        except DryMiss:
            pass
        finally:
            kind.reset(token)
        token = kind.set("regs")
        try:
            choose(profile, corpus, use_llm=True)
        except DryMiss:
            pass
        finally:
            kind.reset(token)
        got = calls[before:]
        side[model] = {
            "hits": sum(1 for c in got if c.hit),
            "misses": sum(1 for c in got if not c.hit),
            "profile_misses": sum(1 for c in got if c.kind == "profile" and not c.hit),
            "regs_misses": sum(1 for c in got if c.kind == "regs" and not c.hit),
            "calls": got,
        }
    os.environ["BRAIN_MODEL_STRONG"] = OPUS

    setup = [c for c in calls[:start] if c.kind in ("profile", "regs")]
    opus_rel_calls = rel["opus"].calls
    strong = setup + opus_rel_calls
    text_chars = sum(c.system_chars + c.user_chars for c in strong)
    img = sum(c.image_tokens for c in strong)
    prompt_tokens_known = OPUS_IN + OPUS_CR
    if len(strong) == OPUS_CALLS and text_chars and prompt_tokens_known > img:
        chars_per_token = text_chars / (prompt_tokens_known - img)
        calibrated = True
    else:
        chars_per_token = 3.5
        calibrated = False
    rebuilt = as_new(strong, chars_per_token)
    # Cached JSON is longer than the model's tokenized output. Scale so the Opus
    # reconstruction matches the 98,058 output tokens in mix-noimage.log.
    out_scale = (OPUS_OUT / rebuilt["out"]) if rebuilt["out"] else 1.0
    opus_items = sum(c.n_items for c in opus_rel_calls) or 1
    opus_out_chars = sum(c.out_chars for c in opus_rel_calls)
    out_per_item = (opus_out_chars / chars_per_token) * out_scale / opus_items

    def priced(these: list[Call], model: str) -> dict[str, Any]:
        parts = miss_bill(these, chars_per_token, out_per_item)
        return {
            "hits": sum(1 for c in these if c.hit),
            "misses": sum(1 for c in these if not c.hit),
            "dollars": round(dollars(model, parts["in"], parts["out"], parts["cache_read"]), 3),
            "in_tokens": round(parts["in"]),
            "out_tokens": round(parts["out"]),
            "cache_read_tokens": round(parts["cache_read"]),
        }

    sonnet_rel = priced(rel["sonnet"].calls, SONNET)
    haiku_rel = priced(rel["haiku"].calls, HAIKU)
    # Profile and regulation review are one call each. Price a miss from the Opus call's
    # tokens (same prompt) at the other model's rates. Not part of the selection estimate.
    opus_profile = [c for c in setup if c.kind == "profile"]
    opus_regs = [c for c in setup if c.kind == "regs"]

    def one_call_dollars(sample: list[Call], model: str) -> float:
        if not sample:
            return 0.0
        parts = as_new(sample[:1], chars_per_token)
        return round(dollars(model, parts["in"], parts["out"] * out_scale, parts["cache_read"]), 3)

    for model, info in side.items():
        info["profile_dollars"] = (
            0.0 if info["profile_misses"] == 0 else one_call_dollars(opus_profile, model)
        )
        info["regs_dollars"] = (
            0.0 if info["regs_misses"] == 0 else one_call_dollars(opus_regs, model)
        )
        info.pop("calls")
    opus_rebuild_dollars = round(
        dollars(OPUS, rebuilt["in"], rebuilt["out"] * out_scale, rebuilt["cache_read"]), 3
    )

    # Rewrite rate from the measured $0.85 file, scaled by prompt characters.
    base_rw = rewrite_stats.get("opus-w70", {})
    base_calls: list[Call] = base_rw.get("calls", [])
    base_chars = sum(c.system_chars + c.user_chars for c in base_calls) or 1
    per_char = REWRITE_DOLLARS / base_chars

    def rewrite_cost(name: str) -> dict[str, Any] | None:
        st = rewrite_stats.get(name)
        if not st:
            return None
        miss_chars = sum(c.system_chars + c.user_chars for c in st["calls"] if not c.hit)
        return {
            "paragraphs": st["paragraphs"],
            "hits": st["hits"],
            "misses": st["misses"],
            "dollars": round(miss_chars * per_char, 3),
            "errors": st["errors"],
        }

    # Cold rewrite of the Opus weight-0.85 paragraph count, for when Sonnet or Haiku
    # scores are missing and the real batches cannot be known.
    proxy_n = len(sets.get("opus-w85", []))
    cold_paragraphs = proxy_n or 267
    cold_rewrite = round(REWRITE_DOLLARS * (cold_paragraphs / 267), 3)

    run1 = ROOT / "out" / "rear-lamp-main-a39acab.json"
    report = {
        "calibrated_to_opus_log": calibrated,
        "chars_per_token": round(chars_per_token, 3),
        "opus_log_rebuild_dollars": opus_rebuild_dollars,
        "out_scale": round(out_scale, 3),
        "strong_calls_seen": len(strong),
        "image_tokens": image_tokens,
        "candidates": len(paragraphs),
        "relevance_batch": rel_batch,
        "rewrite_batch": rw_batch,
        "regulations": [
            {"regulation": c.regulation, "p": c.probability, "selected": c.selected}
            for c in choices
            if c.selected
        ],
        "relevance": {
            name: {
                "model": probe.model,
                "hits": probe.hits,
                "misses": probe.misses,
                "scored": len(probe.scores),
                "errors": probe.errors[:3],
            }
            for name, probe in rel.items()
        },
        "selection_paragraphs": {name: len(rows) for name, rows in sets.items()},
        "rewrite": {name: rewrite_cost(name) for name in rewrite_stats},
        "cold_rewrite_of_opus_w85": {"paragraphs": cold_paragraphs, "dollars": cold_rewrite},
        "run2_relevance": sonnet_rel,
        "run3_relevance": haiku_rel,
        "side_if_strong_model_changes": side,
        "files": {
            "run1": run1.exists(),
            "run2": (ROOT / "out" / "rear-lamp-swing-H-sonnet-w85.json").exists(),
            "run3": (ROOT / "out" / "rear-lamp-swing-H-haiku-rel.json").exists(),
        },
    }
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    if not opus_complete:
        print("opus relevance was not a full cache hit; the payload may not match", file=sys.stderr)
        return 1
    if len(sets.get("opus-w70", [])) != 267:
        print(
            f"weight 0.7 selected {len(sets.get('opus-w70', []))} paragraphs; the log says 267",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
