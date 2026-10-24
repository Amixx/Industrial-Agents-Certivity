"""Lane D: the obligation cut without expert examples, on `main`'s pipeline.

    PYTHONPATH=. uv run python swing/d_cut.py --cut obligation --dry ../cases/dev-rear-lamp ...
    PYTHONPATH=. uv run python swing/d_cut.py --cut obligation ../cases/dev-rear-lamp \
        --team-id team-06 -o ../out/rear-lamp-swing-D-cut-noex.json

Patches `brain.rewrite` at runtime with the rewrite prompt and batch function of `b7d6ee2` (the
code that wrote `out/rear-lamp-mix.json`), then runs `swing/run_costed.py` with the remaining
arguments. `--cut all` keeps `b7d6ee2`'s split-everything rule, so it reproduces
`rear-lamp-mix.json` from the cache; `--cut obligation` swaps in the `_SPLIT_OBLIGATION` rule of
branch `brain-model-mix-examples` (`e5e0d25`), without its expert examples. `--dry` makes no
paid call: every uncached request fails into the deterministic fallback and is counted, with a
token estimate.
"""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

from brain import llm, rewrite
from brain.models import Paragraph

_SPLIT_ALL = """\
- Split until each requirement states exactly one constraint: two limits joined by "and" are two
  requirements; each lettered or numbered list item is its own requirement; each row of a table
  of limits (per pulse, class, colour, test or angle) is its own requirement; an optional or
  alternative case ("Where optional lamps are installed", "as an alternative") is its own
  requirement. Never merge; never leave a list "(a) ... (b) ..." inside one requirement."""

# From branch brain-model-mix-examples at e5e0d25 (brain/brain/rewrite.py).
_SPLIT_OBLIGATION = """\
- Write one requirement per obligation. Keep one obligation's clauses together: a minimum and a
  maximum of the same quantity, a list of items that share one constraint, a constraint and its
  condition or exception. Split only parallel cases that carry their own values or test: each row
  of a table of limits (per pulse, class, band, voltage or test), each list item with its own
  values, each optional or alternative case ("Where optional lamps are installed", "as an
  alternative"). Two different constraints in one sentence are two requirements."""

# The rewrite system prompt of b7d6ee2, with the split rule as a slot.
_SYSTEM = """You turn paragraphs of UN Regulations into engineering requirements for a product.
Write one requirement per obligation, in minimal-edit EARS style:
- "The <subject> shall <constraint>." or, with a condition first, "When/While/Where/If <condition>,
  the <subject> shall <constraint>."
- Name the subject explicitly from the heading path (e.g. "The reversing lamp", "The stop lamp",
  "The retro-reflective device"); never use pronouns.
- Keep numbers, units, tolerances, table and paragraph references, and passive voice verbatim.
- Turn telegraphic provisions into shall-statements ("In height: not less than 250 mm" ->
  "The reversing lamp shall be not less than 250 mm ... above the ground").
- When the paragraph completes its parent's clause (parent_text ends with ":" or "the
  following"), carry the parent's condition into each requirement.
- Fold "However, ..." exceptions into the same requirement as "..., except that ...".
{split}
- Repeat in every split requirement the condition and qualifiers that govern it ("When tested
  in accordance with ...", "if not otherwise agreed between ...", "In case of ..."), so each one
  stands alone.
- Keep a conditional permission as a permission ("... may be installed ... only if ..."); never
  turn "may" into "shall".
- Ignore footnote text and footnote markers glued to words ("vehicles10 10As defined in ...").
- Skip pure definitions, permissions with no constraint, and text that is not an obligation.
Return an empty list for a paragraph with no obligation."""


def _batch(chunk: list[Paragraph], graph, product: str) -> list[rewrite.Draft]:
    """b7d6ee2's batch: no deterministic top-up for paragraphs the model leaves empty."""
    listing = "\n\n".join(
        json.dumps(
            {
                "id": p.id,
                "label": f"{p.regulation} {p.label}",
                "heading_path": rewrite._heading_path(p, graph),
                "parent_text": rewrite._parent_text(p, graph),
                "text": p.text[:4000],
            }
        )
        for p in chunk
    )
    prompt = (
        f"{rewrite._EXAMPLES}\nProduct: {product}\n\nParagraphs (JSON lines):\n\n{listing}\n\n"
        "Return requirements for every paragraph id. `quote` is the source sentence."
    )
    data = llm.complete_json(rewrite._SYSTEM, prompt, rewrite._SCHEMA, tier="bulk")
    by_id = {p.id: p for p in chunk}
    out = []
    for item in data["paragraphs"]:
        p = by_id.get(item["id"])
        if p is None:
            continue
        for r in item["requirements"]:
            text = r["text"].strip()
            if text:
                out.append(rewrite.Draft(p, text, r.get("quote", "").strip()))
    return out


def _dry() -> None:
    """Fail every uncached request instead of paying for it, and count them."""
    real = llm.complete_json
    misses: list[int] = []

    def complete_json(system, content, schema, *, tier="bulk", **kw):
        payload = {
            "provider": llm.provider(),
            "model": llm.model_for(tier),
            "system": system,
            "content": content,
            "schema": schema,
            "effort": kw.get("effort", "medium"),
        }
        if not llm._cache_path(payload).exists():
            misses.append(len(system) + len(json.dumps(content)))
            raise RuntimeError("dry run: not cached")
        return real(system, content, schema, tier=tier, **kw)

    llm.complete_json = complete_json

    def report() -> None:
        tokens = sum(misses) / 3.5
        print(
            f"[dry] {len(misses)} uncached calls, about {tokens / 1e3:.0f}k input tokens; at "
            f"Sonnet $2 / $10 and output 0.5 to 0.6 of input: ${tokens * 2e-6:.2f} in + "
            f"${tokens * 0.55 * 10e-6:.2f} out",
            file=sys.stderr,
        )

    import atexit

    atexit.register(report)


def main() -> None:
    args = sys.argv[1:]
    cut = "obligation"
    if "--cut" in args:
        i = args.index("--cut")
        cut = args[i + 1]
        del args[i : i + 2]
    if "--dry" in args:
        args.remove("--dry")
        _dry()
    rewrite._SYSTEM = _SYSTEM.replace(
        "{split}", _SPLIT_OBLIGATION if cut == "obligation" else _SPLIT_ALL
    )
    rewrite._batch = _batch
    sys.argv = [str(Path(__file__).with_name("run_costed.py")), *args]
    runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
