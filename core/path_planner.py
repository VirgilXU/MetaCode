from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from core.combiner import execute_workflow, load_yaml
from core.context import available_paths
from core.workflow_fixer import infer_failed_step


def _provider_candidates(
    registry: dict[str, dict[str, Any]],
    field: str,
    blocked_ids: set[str],
) -> list[dict[str, Any]]:
    candidates = []
    for metacode_id, identity in registry.items():
        if metacode_id in blocked_ids:
            continue
        if field in identity.get("context_write", []):
            candidates.append(identity)
    return sorted(
        candidates,
        key=lambda identity: (
            len(identity.get("context_read", [])),
            identity["id"],
        ),
    )


def plan_missing_fields(
    registry: dict[str, dict[str, Any]],
    context: dict[str, Any],
    missing_fields: list[str],
    blocked_ids: set[str] | None = None,
    max_depth: int = 4,
) -> dict[str, Any]:
    available = set(available_paths(context))
    blocked = set(blocked_ids or set())
    planned: list[str] = []
    planned_set: set[str] = set()
    reasons: list[str] = []

    def ensure_field(field: str, depth: int, stack: tuple[str, ...]) -> bool:
        if field in available:
            return True
        if depth > max_depth:
            reasons.append(f"max depth reached while resolving {field}")
            return False
        if field in stack:
            reasons.append(f"cycle detected while resolving {field}")
            return False

        for identity in _provider_candidates(registry, field, blocked | planned_set):
            local_available = set(available)
            local_planned = list(planned)
            local_planned_set = set(planned_set)

            ok = True
            for required_field in identity.get("context_read", []):
                if not ensure_field(required_field, depth + 1, stack + (field,)):
                    ok = False
                    break

            if ok:
                metacode_id = identity["id"]
                if metacode_id not in planned_set:
                    planned.append(metacode_id)
                    planned_set.add(metacode_id)
                for output_field in identity.get("context_write", []):
                    available.add(output_field)
                return True

            available.clear()
            available.update(local_available)
            planned.clear()
            planned.extend(local_planned)
            planned_set.clear()
            planned_set.update(local_planned_set)

        reasons.append(f"no provider found for {field}")
        return False

    unresolved = [field for field in missing_fields if not ensure_field(field, 0, ())]
    return {
        "status": "planned" if not unresolved else "not_planned",
        "plan": planned,
        "missing_fields": missing_fields,
        "unresolved": unresolved,
        "reasons": reasons,
    }


def build_planned_workflow(
    workflow: dict[str, Any],
    failed_step: str,
    plan: list[str],
) -> dict[str, Any]:
    planned_workflow = deepcopy(workflow)
    original_steps = list(workflow.get("steps", []))
    planned_steps: list[str] = []
    inserted = False

    for step_id in original_steps:
        if step_id == failed_step and not inserted:
            planned_steps.extend(plan)
            inserted = True
        planned_steps.append(step_id)

    if not inserted:
        raise ValueError(f"failed step not found in workflow steps: {failed_step}")

    planned_workflow["id"] = f"{workflow.get('id', 'workflow')}_planned"
    planned_workflow["name"] = f"{workflow.get('name', workflow.get('id', 'Workflow'))} Planned"
    planned_workflow["steps"] = planned_steps
    planned_workflow["planned_from"] = workflow.get("id")
    planned_workflow["inserted_steps"] = plan
    return planned_workflow


def plan_workflow_fix(root: Path, workflow_path: Path, max_depth: int = 4, repair_id: str | None = None) -> dict[str, Any]:
    from core.registry import build_registry

    workflow = load_yaml(workflow_path)
    original_steps = list(workflow.get("steps", []))
    workflow_id = workflow.get("id", workflow_path.stem)
    result = execute_workflow(
        root,
        workflow_path,
        repair_id=repair_id,
        repair_strategy="planned" if repair_id else None,
        repair_source_workflow_id=workflow_id if repair_id else None,
    )

    if result["status"] == "success":
        return {
            "repair_id": repair_id,
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
            "repair_id": repair_id,
            "status": "not_planned",
            "workflow_id": result["workflow_id"],
            "reason": "could not infer failed step",
            "diagnostic": result,
        }

    registry = build_registry(root)
    plan_result = plan_missing_fields(
        registry,
        result["context"],
        result.get("missing_fields", []),
        blocked_ids=set(result.get("executed_steps", [])) | {failed_step},
        max_depth=max_depth,
    )
    if plan_result["status"] != "planned":
        return {
            "repair_id": repair_id,
            "status": "not_planned",
            "workflow_id": result["workflow_id"],
            "failed_step": failed_step,
            "reason": "no complete plan found",
            "plan_result": plan_result,
        }

    planned_workflow = build_planned_workflow(workflow, failed_step, plan_result["plan"])
    output_dir = root / "workflows" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{workflow_path.stem}.planned.yaml"
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(planned_workflow, handle, allow_unicode=True, sort_keys=False)

    verification = execute_workflow(
        root,
        output_path,
        repair_id=repair_id,
        repair_strategy="planned" if repair_id else None,
        repair_source_workflow_id=workflow_id if repair_id else None,
    )
    return {
        "repair_id": repair_id,
        "status": "planned" if verification["status"] == "success" else "planned_but_failed",
        "workflow_id": result["workflow_id"],
        "failed_step": failed_step,
        "inserted": plan_result["plan"],
        "output_path": str(output_path),
        "verification_status": verification["status"],
        "verification_reason": verification.get("reason"),
        "planned_steps": planned_workflow["steps"],
        "plan_result": plan_result,
    }
