from __future__ import annotations

import importlib.util
import json
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

from core.context import append_error, append_log, available_paths, create_context, has_path, now_iso
from core.recommender import format_suggestions, suggest_for_missing_fields
from core.registry import build_registry


class WorkflowError(RuntimeError):
    def __init__(
        self,
        message: str,
        missing_fields: list[str] | None = None,
        suggestions: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.missing_fields = missing_fields or []
        self.suggestions = suggestions or []


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_runner(identity: dict[str, Any]):
    runner_path = Path(identity["_base_dir"]) / identity["runner"]
    if not runner_path.exists():
        raise WorkflowError(f"runner not found for {identity['id']}: {runner_path}")

    module_name = "metacode_runner_" + identity["id"].replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, runner_path)
    if spec is None or spec.loader is None:
        raise WorkflowError(f"failed to load runner spec: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run"):
        raise WorkflowError(f"runner has no run(context): {runner_path}")
    return module.run


def write_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def execute_workflow(root: Path, workflow_path: Path) -> dict[str, Any]:
    run_id = str(uuid.uuid4())
    started_at = now_iso()
    started = time.perf_counter()
    workflow = load_yaml(workflow_path)
    workflow_id = workflow.get("id", workflow_path.stem)
    context = create_context(workflow.get("inputs", {}))
    registry = build_registry(root)
    steps = workflow.get("steps", [])
    executed: list[str] = []

    try:
        if not steps:
            raise WorkflowError("workflow has no steps")

        for step_id in steps:
            if step_id not in registry:
                raise WorkflowError(f"unknown metacode id: {step_id}")

            identity = registry[step_id]
            missing = [field for field in identity["context_read"] if not has_path(context, field)]
            if missing:
                suggestions = suggest_for_missing_fields(
                    registry,
                    context,
                    missing,
                    exclude_ids=set(executed) | {step_id},
                )
                raise WorkflowError(
                    f"{step_id} missing context field(s): {', '.join(missing)}. "
                    f"available: {', '.join(available_paths(context))}. "
                    f"suggestions: {format_suggestions(suggestions)}",
                    missing_fields=missing,
                    suggestions=suggestions,
                )

            append_log(context, "step_start", step_id=step_id)
            runner = load_runner(identity)
            context = runner(context)
            executed.append(step_id)

            missing_outputs = [
                field for field in identity["context_write"] if not has_path(context, field)
            ]
            if missing_outputs:
                raise WorkflowError(
                    f"{step_id} did not write expected field(s): {', '.join(missing_outputs)}"
                )
            append_log(context, "step_success", step_id=step_id)

        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        ended_at = now_iso()
        record = {
            "run_id": run_id,
            "time": ended_at,
            "started_at": started_at,
            "ended_at": ended_at,
            "workflow_id": workflow_id,
            "workflow_path": str(workflow_path),
            "status": "success",
            "steps": executed,
            "steps_total": len(steps),
            "steps_success": len(executed),
            "duration_ms": duration_ms,
            "outputs": context.get("artifacts", {}),
        }
        write_jsonl(root / "logs" / "run_log.jsonl", record)
        return {"status": "success", "workflow_id": workflow_id, "context": context, **record}

    except Exception as exc:
        append_error(context, str(exc), workflow_id=workflow_id)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        ended_at = now_iso()
        missing_fields = exc.missing_fields if isinstance(exc, WorkflowError) else []
        suggestions = exc.suggestions if isinstance(exc, WorkflowError) else []
        failed_step = infer_step_from_error(str(exc), steps, executed)
        record = {
            "run_id": run_id,
            "time": ended_at,
            "started_at": started_at,
            "ended_at": ended_at,
            "workflow_id": workflow_id,
            "workflow_path": str(workflow_path),
            "status": "failed",
            "executed_steps": executed,
            "steps_total": len(steps),
            "steps_success": len(executed),
            "failed_step": failed_step,
            "reason": str(exc),
            "missing_fields": missing_fields,
            "suggestions": suggestions,
            "context_keys": available_paths(context),
            "duration_ms": duration_ms,
        }
        write_jsonl(root / "logs" / "failure_log.jsonl", record)
        return {"status": "failed", "workflow_id": workflow_id, "context": context, **record}


def infer_step_from_error(reason: str, steps: list[str], executed: list[str]) -> str | None:
    remaining = steps[len(executed) :]
    for step_id in remaining:
        if reason.startswith(step_id):
            return step_id
    return remaining[0] if remaining else None
