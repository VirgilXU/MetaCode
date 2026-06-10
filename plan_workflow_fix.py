from __future__ import annotations

import json
import sys
from pathlib import Path

from core.path_planner import plan_workflow_fix


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python plan_workflow_fix.py workflows/<workflow>.yaml")
        return 2

    root = Path(__file__).resolve().parent
    workflow_path = Path(sys.argv[1])
    if not workflow_path.is_absolute():
        workflow_path = root / workflow_path

    result = plan_workflow_fix(root, workflow_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"planned", "not_needed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
