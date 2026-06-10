from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from core.combiner import execute_workflow, load_yaml


def infer_failed_step(reason: str, steps: list[str], executed_steps: list[str]) -> str | None:
    remaining = steps[len(executed_steps) :]
    for step_id in remaining:
        if reason.startswith(step_id):
            return step_id
    return remaining[0] if remaining else None


def choose_ready_suggestion(suggestions: list[dict[str, Any]]) -> dict[str, Any] | None:
    for suggestion in suggestions:
        if suggestion.get("ready"):
            return suggestion
    return None


def build_fixed_workflow(
    workflow: dict[str, Any],
    failed_step: str,
    insert_step: str,
) -> dict[str, Any]:
    fixed = deepcopy(workflow)
    original_steps = list(workflow.get("steps", []))
    fixed_steps: list[str] = []
    inserted = False

    for step_id in original_steps:
        if step_id == failed_step and not inserted:
            fixed_steps.append(insert_step)
            inserted = True
        fixed_steps.append(step_id)

    if not inserted:
        raise ValueError(f"failed step not found in workflow steps: {failed_step}")

    fixed["id"] = f"{workflow.get('id', 'workflow')}_fixed"
    fixed["name"] = f"{workflow.get('name', workflow.get('id', 'Workflow'))} Fixed"
    fixed["steps"] = fixed_steps
    fixed["fixed_from"] = workflow.get("id")
    fixed["inserted_steps"] = [insert_step]
    return fixed


def fix_workflow(root: Path, workflow_path: Path) -> dict[str, Any]:
    workflow = load_yaml(workflow_path)
    original_steps = list(workflow.get("steps", []))
    result = execute_workflow(root, workflow_path)

    if result["status"] == "success":
        return {
            "status": "not_needed",
            "workflow_id": result["workflow_id"],
            "reason": "workflow already succeeds",
        }

    failed_step = infer_failed_step(
        result.get("reason", ""),
        original_steps,
        result.get("executed_steps", []),
    )
    if not failed_step:
        return {
            "status": "not_fixed",
            "workflow_id": result["workflow_id"],
            "reason": "could not infer failed step",
            "diagnostic": result,
        }

    suggestion = choose_ready_suggestion(result.get("suggestions", []))
    if not suggestion:
        return {
            "status": "not_fixed",
            "workflow_id": result["workflow_id"],
            "reason": "no ready suggestion available",
            "diagnostic": result,
        }

    fixed = build_fixed_workflow(workflow, failed_step, suggestion["metacode_id"])
    output_dir = root / "workflows" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{workflow_path.stem}.fixed.yaml"
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(fixed, handle, allow_unicode=True, sort_keys=False)

    verification = execute_workflow(root, output_path)
    return {
        "status": "fixed" if verification["status"] == "success" else "fixed_but_failed",
        "workflow_id": result["workflow_id"],
        "failed_step": failed_step,
        "inserted": suggestion["metacode_id"],
        "output_path": str(output_path),
        "verification_status": verification["status"],
        "verification_reason": verification.get("reason"),
        "fixed_steps": fixed["steps"],
    }
