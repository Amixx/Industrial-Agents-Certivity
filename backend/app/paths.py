import os
from pathlib import Path

ROOT = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2])
CASES = ROOT / "cases"
REGULATIONS = ROOT / "regulations"
UPDATES = ROOT / "data" / "regulation-updates"
FRONTEND_BUILD = ROOT / "frontend" / "build"
DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parents[1] / ".data")
