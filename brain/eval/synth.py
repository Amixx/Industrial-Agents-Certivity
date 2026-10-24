"""Tier A synthetic cases: ablations of the real rear-lamp gold, so the labels stay expert-made.

    uv run python -m eval.synth            # writes data/synthetic/tierA-*/{spec.md,expected.json}

Each gold requirement is tagged with the lamp function its paragraph belongs to (by section
number, read off the regulations' own headings). A variant spec drops some functions; its gold
is the subset whose tag is still present, plus the general provisions. Without electronics the
EMC regulation (R10) drops out; without a retro-reflector, R150 does.
"""

from __future__ import annotations

import json
from pathlib import Path

from brain.paths import CASES, DATA

# (regulation, paragraph prefix) -> function. Anything untagged is a general provision.
SECTIONS = {
    ("UN R48", "6.4"): "reversing",
    ("UN R48", "6.7"): "stop",
    ("UN R48", "6.10"): "position",
    ("UN R48", "6.14"): "retro",
    ("UN R148", "5.2"): "position",
    ("UN R148", "5.5"): "stop",
    ("UN R148", "5.8"): "reversing",
    ("UN R148", "Annex 8 1.2.1"): "reversing",
}
WHOLE = {"UN R150": "retro", "UN R10": "electronics"}

PARTS = {
    "position": ("Rear position lamp", "Rear position signalling (presence/visibility)"),
    "stop": ("Stop lamp", "Braking indication (stop lamp)"),
    "reversing": ("Reversing lamp", "Reversing illumination"),
    "retro": ("Retro-reflector", "Passive conspicuity (retro-reflector)"),
}

VARIANTS = {
    "tierA-stop-lamp-led": {"stop", "electronics"},
    "tierA-position-retro-led": {"position", "retro", "electronics"},
    "tierA-reversing-filament": {"reversing"},
    "tierA-stop-position-filament": {"stop", "position"},
    "tierA-full-filament": {"stop", "position", "reversing", "retro"},
}


def tag(requirement: dict) -> str:
    s = requirement["source"]
    if s["regulation"] in WHOLE:
        return WHOLE[s["regulation"]]
    label = s.get("paragraph", "")
    for (reg, prefix), function in SECTIONS.items():
        if s["regulation"] == reg and (label == prefix or label.startswith(prefix + ".")):
            return function
    return "general"


def spec(functions: set[str]) -> str:
    parts = [PARTS[f] for f in ("position", "stop", "reversing", "retro") if f in functions]
    light = "LED modules on PCB" if "electronics" in functions else "Filament bulb in socket"
    lines = [
        "# spec: Rear lamp variant",
        "",
        "## Product Type",
        "",
        "Rear lamp — exterior lighting & signalling module in a single housing.",
        "",
        "## Vehicle Category",
        "",
        "M1 — passenger car.",
        "",
        "## Function",
        "",
    ]
    lines += [f"- {fn}" for _, fn in parts] + ["", "## Main Parts", ""]
    lines += [f"- {part}" for part, _ in parts] + [
        "- Outer lens",
        "",
        "## Materials",
        "",
        "| Component | Typical material(s) |",
        "| --- | --- |",
        "| Outer lens | PMMA |",
        f"| Light source | {light} |",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    expected = json.loads((CASES / "dev-rear-lamp" / "expected.json").read_text())
    for name, functions in VARIANTS.items():
        keep = functions | {"general"}
        reqs = [r for r in expected["requirements"] if tag(r) in keep]
        if "position" not in functions and "stop" not in functions and "reversing" not in functions:
            reqs = [r for r in reqs if r["source"]["regulation"] not in ("UN R148", "UN R48")]
        folder = DATA / "synthetic" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "spec.md").write_text(spec(functions))
        (folder / "expected.json").write_text(
            json.dumps({"team_id": "team-00", "case_id": name, "requirements": reqs}, indent=1)
        )
        regs = sorted({r["source"]["regulation"] for r in reqs})
        print(f"{name:32s} {len(reqs):3d} requirements  {', '.join(regs)}")
    return 0


def cases(root: Path = DATA / "synthetic") -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.iterdir() if (p / "expected.json").exists())


if __name__ == "__main__":
    raise SystemExit(main())
