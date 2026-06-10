from __future__ import annotations

import json
from pathlib import Path

from core.capability_graph import summarize_graph


def main() -> int:
    root = Path(__file__).resolve().parent
    result = summarize_graph(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
