from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

from core.registry import build_registry


SKIP_WORKFLOWS = {
    "broken_missing_clean_text.yaml",
    "broken_missing_summary_chain.yaml",
}


def load_workflows(root: Path):
    for workflow_path in sorted((root / "workflows").glob("*.yaml")):
        if workflow_path.name in SKIP_WORKFLOWS:
            continue
        with workflow_path.open("r", encoding="utf-8") as handle:
            workflow = yaml.safe_load(handle) or {}
        yield workflow_path, workflow


def analyze(root: Path) -> dict:
    registry = build_registry(root)
    workflows = list(load_workflows(root))
    usage = Counter()
    total_steps = 0
    for _path, workflow in workflows:
        steps = workflow.get("steps", [])
        usage.update(steps)
        total_steps += len(steps)

    reused = {metacode_id: count for metacode_id, count in usage.items() if count >= 2}
    unused = sorted(set(registry) - set(usage))
    return {
        "metacode_count": len(registry),
        "workflow_count": len(workflows),
        "total_workflow_steps": total_steps,
        "reused_metacode_count": len(reused),
        "unused_metacode_count": len(unused),
        "usage": dict(sorted(usage.items(), key=lambda item: (-item[1], item[0]))),
        "unused": unused,
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    result = analyze(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
