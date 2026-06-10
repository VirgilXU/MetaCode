from __future__ import annotations

import json
from pathlib import Path

from core.monitoring_store import export_monitoring_data


def main() -> int:
    root = Path(__file__).resolve().parent
    payload = export_monitoring_data(root)
    result = {
        "status": "exported",
        "database_path": payload["database_path"],
        "exports": [
            "dashboard_summary.json",
            "runs.json",
            "failures.json",
            "stages.json",
            "workflow_graph.json",
            "reuse_summary.json",
            "capability_graph.json",
            "capability_graph_summary.json",
        ],
        "run_count": len(payload["runs"]),
        "stage_count": len(payload["stages"]),
        "workflow_count": len(payload["workflows"]),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
