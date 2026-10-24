import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]  # the brain/ folder at the repo root
ROOT = Path(os.environ.get("REPO_ROOT") or PROJECT.parent)
CASES = ROOT / "cases"
REGULATIONS = ROOT / "regulations"
INDEX = REGULATIONS / "index.json"
PDFS = REGULATIONS / "pdf"
TOOLS = ROOT / "tools"
DATA = PROJECT / "data"
CORPUS = DATA / "corpus"
CACHE = DATA / "cache"
