import os
from pathlib import Path

ROOT = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[3])
CASES = ROOT / "cases"
REGULATIONS = ROOT / "regulations"
UPDATES = ROOT / "data" / "regulation-updates"
BRIEFS = ROOT / "data" / "briefs"
BRAIN = ROOT / "brain"
BRAIN_PYTHON = BRAIN / ".venv" / "bin" / "python"
BRAIN_RUNNER = Path(__file__).resolve().parents[1] / "brain_runner.py"
FRONTEND_BUILD = ROOT / "web" / "frontend" / "build"
DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parents[1] / ".data")
