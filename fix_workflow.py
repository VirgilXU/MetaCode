from __future__ import annotations

import json
import sys
from pathlib import Path

from core.workflow_fixer import fix_workflow


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python fix_workflow.py workflows/<workflow>.yaml")
        return 2

    root = Path(__file__).resolve().parent
    workflow_path = Path(sys.argv[1])
    if not workflow_path.is_absolute():
        workflow_path = root / workflow_path

    result = fix_workflow(root, workflow_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"fixed", "not_needed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
