from __future__ import annotations

import json
from pathlib import Path

from core.combiner import execute_workflow


SKIP_WORKFLOWS = {
    "broken_missing_clean_text.yaml",
    "broken_missing_summary_chain.yaml",
}


def main() -> int:
    root = Path(__file__).resolve().parent
    results = []
    for workflow_path in sorted((root / "workflows").glob("*.yaml")):
        if workflow_path.name in SKIP_WORKFLOWS:
            continue
        result = execute_workflow(root, workflow_path)
        results.append(
            {
                "workflow_id": result["workflow_id"],
                "status": result["status"],
                "steps": result.get("steps") or result.get("executed_steps"),
                "reason": result.get("reason"),
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(item["status"] == "success" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
