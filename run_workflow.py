from __future__ import annotations

import json
import sys
from pathlib import Path

from core.combiner import execute_workflow


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run_workflow.py workflows/<workflow>.yaml")
        return 2

    root = Path(__file__).resolve().parent
    workflow_path = Path(sys.argv[1])
    if not workflow_path.is_absolute():
        workflow_path = root / workflow_path

    result = execute_workflow(root, workflow_path)
    summary = {
        "workflow_id": result["workflow_id"],
        "status": result["status"],
        "steps": result.get("steps") or result.get("executed_steps"),
        "outputs": result.get("outputs", {}),
        "reason": result.get("reason"),
        "missing_fields": result.get("missing_fields", []),
        "suggestions": result.get("suggestions", []),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
