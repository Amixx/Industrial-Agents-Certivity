import os
from pathlib import Path

ROOT = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2])
CASES = ROOT / "cases"
REGULATIONS = ROOT / "regulations"
FRONTEND_BUILD = ROOT / "frontend" / "build"
