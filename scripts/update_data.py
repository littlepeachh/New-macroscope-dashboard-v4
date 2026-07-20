from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import update_all  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(update_all(), ensure_ascii=False, indent=2))
