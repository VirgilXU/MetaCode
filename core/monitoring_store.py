from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from analyze_reuse import analyze as analyze_reuse
from core.capability_graph import build_capability_graph, summarize_graph
from core.registry import build_registry


STAGE_RE = re.compile(r"Stage\s+(\d+)\s+验证报告\.md$")
BROKEN_WORKFLOWS = {
    "broken_missing_clean_text.yaml",
    "broken_missing_summary_chain.yaml",
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def infer_failed_step(reason: str | None) -> str | None:
    if not reason:
        return None
    first = reason.split(" ", 1)[0]
    return first if "." in first else None


def normalize_run_record(record: dict[str, Any], index: int, source_log: str) -> dict[str, Any]:
    status = record.get("status", "unknown")
    steps = record.get("steps") or record.get("executed_steps") or []
    run_id = record.get("run_id") or f"{source_log}-{index:06d}-{record.get('workflow_id', 'workflow')}"
    ended_at = record.get("ended_at") or record.get("time")
    return {
        "run_id": run_id,
        "workflow_id": record.get("workflow_id", ""),
        "workflow_path": record.get("workflow_path"),
        "status": status,
        "started_at": record.get("started_at") or record.get("time"),
        "ended_at": ended_at,
        "duration_ms": record.get("duration_ms", 0),
        "steps": steps,
        "steps_total": record.get("steps_total", len(steps)),
        "steps_success": record.get("steps_success", len(steps)),
        "failed_step": record.get("failed_step") or infer_failed_step(record.get("reason")),
        "reason": record.get("reason"),
        "missing_fields": record.get("missing_fields", []),
        "suggestions": record.get("suggestions", []),
        "outputs": record.get("outputs", {}),
        "context_keys": record.get("context_keys", []),
        "source_log": source_log,
    }


def collect_runs(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    raw_runs = read_jsonl(root / "logs" / "run_log.jsonl")
    raw_failures = read_jsonl(root / "logs" / "failure_log.jsonl")
    for index, record in enumerate(raw_runs, start=1):
        records.append(normalize_run_record(record, index, "run_log"))
    for index, record in enumerate(raw_failures, start=1):
        records.append(normalize_run_record(record, index, "failure_log"))
    return sorted(records, key=lambda item: item.get("ended_at") or "")


def collect_stage_reports(root: Path) -> list[dict[str, Any]]:
    stages = []
    for report_path in sorted((root / "docs").glob("Stage * 验证报告.md")):
        match = STAGE_RE.search(report_path.name)
        if not match:
            continue
        stat = report_path.stat()
        stage_id = int(match.group(1))
        stages.append(
            {
                "stage_id": stage_id,
                "title": f"Stage {stage_id}",
                "status": "completed",
                "report_path": str(report_path),
                "report_size": stat.st_size,
                "updated_at": str(stat.st_mtime),
            }
        )
    return sorted(stages, key=lambda stage: stage["stage_id"])


def classify_workflow(path: Path, workflow: dict[str, Any]) -> str:
    if workflow.get("fixed_from"):
        return "generated_fixed"
    if workflow.get("planned_from"):
        return "generated_planned"
    if path.name in BROKEN_WORKFLOWS:
        return "intentional_failure"
    return "stable"


def collect_workflows(root: Path) -> list[dict[str, Any]]:
    workflows = []
    for workflow_path in sorted((root / "workflows").glob("**/*.yaml")):
        with workflow_path.open("r", encoding="utf-8") as handle:
            workflow = yaml.safe_load(handle) or {}
        inputs = workflow.get("inputs", {})
        workflows.append(
            {
                "workflow_id": workflow.get("id", workflow_path.stem),
                "name": workflow.get("name", workflow.get("id", workflow_path.stem)),
                "workflow_path": str(workflow_path),
                "status_type": classify_workflow(workflow_path, workflow),
                "steps": workflow.get("steps", []),
                "generated_from": workflow.get("fixed_from") or workflow.get("planned_from"),
                "inserted_steps": workflow.get("inserted_steps", []),
                "output_path": inputs.get("output_path"),
            }
        )
    return workflows


def infer_repair_strategy(workflow_id: str, workflow: dict[str, Any] | None = None) -> str | None:
    status_type = (workflow or {}).get("status_type")
    if status_type == "generated_fixed" or workflow_id.endswith("_fixed"):
        return "fixed"
    if status_type == "generated_planned" or workflow_id.endswith("_planned"):
        return "planned"
    return None


def infer_repair_source(workflow_id: str, strategy: str, workflow: dict[str, Any] | None = None) -> str:
    generated_from = (workflow or {}).get("generated_from")
    if generated_from:
        return generated_from
    suffix = f"_{strategy}"
    if workflow_id.endswith(suffix):
        return workflow_id[: -len(suffix)]
    return workflow_id


def rate(success_count: int, attempt_count: int) -> float:
    return round((success_count / attempt_count) * 100, 1) if attempt_count else 0.0


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def elapsed_ms(start: str | None, end: str | None) -> float | None:
    start_time = parse_time(start)
    end_time = parse_time(end)
    if not start_time or not end_time:
        return None
    return round((end_time - start_time).total_seconds() * 1000, 3)


def build_repair_metrics(runs: list[dict[str, Any]], workflows: list[dict[str, Any]]) -> dict[str, Any]:
    workflow_by_id = {workflow["workflow_id"]: workflow for workflow in workflows}
    by_strategy: dict[str, dict[str, Any]] = {}
    by_workflow: dict[str, dict[str, Any]] = {}
    recent_attempts: list[dict[str, Any]] = []

    for run in runs:
        workflow_id = run.get("workflow_id", "")
        workflow = workflow_by_id.get(workflow_id)
        strategy = infer_repair_strategy(workflow_id, workflow)
        if not strategy:
            continue

        source_workflow_id = infer_repair_source(workflow_id, strategy, workflow)
        success = run.get("status") == "success"
        status_key = "success_count" if success else "failed_count"

        strategy_row = by_strategy.setdefault(
            strategy,
            {
                "id": strategy,
                "strategy": strategy,
                "attempt_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "repair_workflows": {},
                "source_workflows": {},
                "latest_status": "",
            },
        )
        strategy_row["attempt_count"] += 1
        strategy_row[status_key] += 1
        strategy_row["repair_workflows"][workflow_id] = strategy_row["repair_workflows"].get(workflow_id, 0) + 1
        strategy_row["source_workflows"][source_workflow_id] = (
            strategy_row["source_workflows"].get(source_workflow_id, 0) + 1
        )
        strategy_row["latest_status"] = run.get("status", "unknown")

        workflow_row = by_workflow.setdefault(
            source_workflow_id,
            {
                "id": source_workflow_id,
                "source_workflow_id": source_workflow_id,
                "attempt_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "strategies": {},
                "repair_workflows": {},
                "latest_repair_workflow_id": "",
                "latest_status": "",
            },
        )
        workflow_row["attempt_count"] += 1
        workflow_row[status_key] += 1
        workflow_row["strategies"][strategy] = workflow_row["strategies"].get(strategy, 0) + 1
        workflow_row["repair_workflows"][workflow_id] = workflow_row["repair_workflows"].get(workflow_id, 0) + 1
        workflow_row["latest_repair_workflow_id"] = workflow_id
        workflow_row["latest_status"] = run.get("status", "unknown")

        recent_attempts.append(
            {
                "run_id": run.get("run_id"),
                "workflow_id": workflow_id,
                "source_workflow_id": source_workflow_id,
                "strategy": strategy,
                "status": run.get("status", "unknown"),
                "ended_at": run.get("ended_at"),
                "duration_ms": run.get("duration_ms", 0),
            }
        )

    for row in by_strategy.values():
        row["success_rate"] = rate(row["success_count"], row["attempt_count"])
        row["repair_workflow_count"] = len(row["repair_workflows"])
        row["source_workflow_count"] = len(row["source_workflows"])

    for row in by_workflow.values():
        row["success_rate"] = rate(row["success_count"], row["attempt_count"])
        row["repair_workflow_count"] = len(row["repair_workflows"])

    strategy_rows = sorted(by_strategy.values(), key=lambda row: (-row["attempt_count"], row["strategy"]))
    workflow_rows = sorted(by_workflow.values(), key=lambda row: (-row["attempt_count"], row["source_workflow_id"]))
    attempt_count = sum(row["attempt_count"] for row in strategy_rows)
    success_count = sum(row["success_count"] for row in strategy_rows)
    failed_count = attempt_count - success_count
    fixed_row = by_strategy.get("fixed", {})
    planned_row = by_strategy.get("planned", {})

    return {
        "summary": {
            "status": "computed",
            "attempt_count": attempt_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "repair_success_rate": rate(success_count, attempt_count),
            "fixed_attempt_count": fixed_row.get("attempt_count", 0),
            "fixed_success_count": fixed_row.get("success_count", 0),
            "fixed_success_rate": rate(fixed_row.get("success_count", 0), fixed_row.get("attempt_count", 0)),
            "planned_attempt_count": planned_row.get("attempt_count", 0),
            "planned_success_count": planned_row.get("success_count", 0),
            "planned_success_rate": rate(planned_row.get("success_count", 0), planned_row.get("attempt_count", 0)),
            "source_workflow_count": len(workflow_rows),
            "repair_workflow_count": len({attempt["workflow_id"] for attempt in recent_attempts}),
            "latest_attempt": recent_attempts[-1] if recent_attempts else None,
        },
        "by_strategy": strategy_rows,
        "by_workflow": workflow_rows,
        "recent_attempts": list(reversed(recent_attempts[-8:])),
    }


def compact_suggestion(suggestion: dict[str, Any]) -> dict[str, Any]:
    return {
        "metacode_id": suggestion.get("metacode_id"),
        "name": suggestion.get("name"),
        "category": suggestion.get("category"),
        "provides": suggestion.get("provides", []),
        "requires": suggestion.get("requires", []),
        "unmet_inputs": suggestion.get("unmet_inputs", []),
        "ready": bool(suggestion.get("ready")),
        "score": suggestion.get("score"),
    }


def compact_failure(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if not run:
        return None
    return {
        "run_id": run.get("run_id"),
        "workflow_id": run.get("workflow_id"),
        "workflow_path": run.get("workflow_path"),
        "status": run.get("status"),
        "ended_at": run.get("ended_at"),
        "failed_step": run.get("failed_step"),
        "reason": run.get("reason"),
        "missing_fields": run.get("missing_fields", []),
        "suggestions": [compact_suggestion(suggestion) for suggestion in run.get("suggestions", [])],
    }


def build_event_rollup(events: list[dict[str, Any]], key: str, id_key: str) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for event in events:
        row_id = event[key]
        row = rows.setdefault(
            row_id,
            {
                "id": row_id,
                id_key: row_id,
                "event_count": 0,
                "closed_success_count": 0,
                "closed_failed_count": 0,
                "linked_failure_count": 0,
                "latest_event_id": "",
                "latest_status": "",
            },
        )
        row["event_count"] += 1
        if event["event_status"] == "closed_success":
            row["closed_success_count"] += 1
        if event["event_status"] == "closed_failed":
            row["closed_failed_count"] += 1
        if event["failure_link_status"] == "linked":
            row["linked_failure_count"] += 1
        row["latest_event_id"] = event["repair_id"]
        row["latest_status"] = event["event_status"]

    for row in rows.values():
        row["success_rate"] = rate(row["closed_success_count"], row["event_count"])
        row["failure_link_rate"] = rate(row["linked_failure_count"], row["event_count"])
    return sorted(rows.values(), key=lambda row: (-row["event_count"], row[id_key]))


def build_repair_events(runs: list[dict[str, Any]], workflows: list[dict[str, Any]]) -> dict[str, Any]:
    workflow_by_id = {workflow["workflow_id"]: workflow for workflow in workflows}
    latest_failure_by_workflow: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []

    for run in runs:
        workflow_id = run.get("workflow_id", "")
        if run.get("status") == "failed":
            latest_failure_by_workflow[workflow_id] = run
            continue

        workflow = workflow_by_id.get(workflow_id)
        strategy = infer_repair_strategy(workflow_id, workflow)
        if not strategy:
            continue

        source_workflow_id = infer_repair_source(workflow_id, strategy, workflow)
        failure = latest_failure_by_workflow.get(source_workflow_id)
        suggestions = [compact_suggestion(suggestion) for suggestion in (failure or {}).get("suggestions", [])]
        suggested_metacodes = [suggestion["metacode_id"] for suggestion in suggestions if suggestion.get("metacode_id")]
        inserted_steps = list((workflow or {}).get("inserted_steps") or suggested_metacodes)
        verification_status = run.get("status", "unknown")
        event_status = "closed_success" if verification_status == "success" else "closed_failed"

        events.append(
            {
                "repair_id": f"repair-{run.get('run_id')}",
                "event_status": event_status,
                "failure_link_status": "linked" if failure else "unlinked",
                "source_workflow_id": source_workflow_id,
                "failure_run_id": failure.get("run_id") if failure else None,
                "failure_ended_at": failure.get("ended_at") if failure else None,
                "failed_step": failure.get("failed_step") if failure else None,
                "missing_fields": failure.get("missing_fields", []) if failure else [],
                "suggestions": suggestions,
                "suggested_metacodes": suggested_metacodes,
                "ready_suggestion_count": len([suggestion for suggestion in suggestions if suggestion.get("ready")]),
                "strategy": strategy,
                "generated_workflow_id": workflow_id,
                "generated_workflow_path": (workflow or {}).get("workflow_path") or run.get("workflow_path"),
                "inserted_steps": inserted_steps,
                "verification_run_id": run.get("run_id"),
                "verification_status": verification_status,
                "verification_ended_at": run.get("ended_at"),
                "verification_duration_ms": run.get("duration_ms", 0),
                "event_latency_ms": elapsed_ms(failure.get("ended_at") if failure else None, run.get("ended_at")),
                "failure": compact_failure(failure),
            }
        )

    closed_success_count = len([event for event in events if event["event_status"] == "closed_success"])
    linked_event_count = len([event for event in events if event["failure_link_status"] == "linked"])
    event_count = len(events)
    by_strategy = build_event_rollup(events, "strategy", "strategy")
    by_workflow = build_event_rollup(events, "source_workflow_id", "source_workflow_id")
    return {
        "summary": {
            "status": "computed",
            "event_count": event_count,
            "closed_success_count": closed_success_count,
            "closed_failed_count": event_count - closed_success_count,
            "event_success_rate": rate(closed_success_count, event_count),
            "linked_event_count": linked_event_count,
            "unlinked_event_count": event_count - linked_event_count,
            "failure_link_rate": rate(linked_event_count, event_count),
            "strategy_count": len(by_strategy),
            "source_workflow_count": len(by_workflow),
            "generated_workflow_count": len({event["generated_workflow_id"] for event in events}),
            "latest_event": events[-1] if events else None,
        },
        "events": events,
        "recent_events": list(reversed(events[-8:])),
        "by_strategy": by_strategy,
        "by_workflow": by_workflow,
    }


def dashboard_summary(
    reuse_summary: dict[str, Any],
    graph_summary: dict[str, Any],
    runs: list[dict[str, Any]],
    stages: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = [run for run in runs if run["status"] == "failed"]
    successes = [run for run in runs if run["status"] == "success"]
    latest_run = runs[-1] if runs else None
    generated_workflows = [
        workflow for workflow in workflows if str(workflow["status_type"]).startswith("generated")
    ]
    intentional_failures = [
        workflow for workflow in workflows if workflow["status_type"] == "intentional_failure"
    ]
    stable_workflows = [workflow for workflow in workflows if workflow["status_type"] == "stable"]
    success_rate = round((len(successes) / len(runs)) * 100, 1) if runs else 0
    current_stage = max((stage["stage_id"] for stage in stages), default=None)
    return {
        "current_stage": current_stage,
        "stage_report_count": len(stages),
        "stage_range": {
            "first": min((stage["stage_id"] for stage in stages), default=None),
            "last": current_stage,
        },
        "metacode_count": reuse_summary["metacode_count"],
        "stable_workflow_count": reuse_summary["workflow_count"],
        "workflow_file_count": len(workflows),
        "stable_workflow_file_count": len(stable_workflows),
        "generated_workflow_count": len(generated_workflows),
        "intentional_failure_workflow_count": len(intentional_failures),
        "run_count": len(runs),
        "success_run_count": len(successes),
        "failure_run_count": len(failures),
        "success_rate": success_rate,
        "edge_count": graph_summary["edge_count"],
        "field_count": graph_summary["field_count"],
        "unresolved_field_count": len(graph_summary["unresolved_fields"]),
        "last_exported_at": datetime.now(timezone.utc).isoformat(),
        "latest_run": latest_run,
    }


def write_sqlite_database(root: Path, payload: dict[str, Any]) -> Path:
    monitoring_dir = root / "monitoring"
    db_path = monitoring_dir / "metacode_monitor.db"
    schema_path = monitoring_dir / "schema.sql"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        for table in ("runs", "workflows", "stages", "repair_events", "metacodes", "graph_edges", "summaries"):
            conn.execute(f"DELETE FROM {table}")

        for run in payload["runs"]:
            conn.execute(
                """
                INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["run_id"],
                    run["workflow_id"],
                    run.get("workflow_path"),
                    run["status"],
                    run.get("started_at"),
                    run.get("ended_at"),
                    run.get("duration_ms"),
                    run.get("steps_total"),
                    run.get("steps_success"),
                    run.get("failed_step"),
                    run.get("reason"),
                    json.dumps(run.get("missing_fields", []), ensure_ascii=False),
                    json.dumps(run.get("suggestions", []), ensure_ascii=False),
                    json.dumps(run.get("outputs", {}), ensure_ascii=False),
                    json.dumps(run.get("context_keys", []), ensure_ascii=False),
                    run.get("source_log"),
                ),
            )

        for workflow in payload["workflows"]:
            conn.execute(
                "INSERT INTO workflows VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    workflow["workflow_id"],
                    workflow["name"],
                    workflow["workflow_path"],
                    workflow["status_type"],
                    json.dumps(workflow["steps"], ensure_ascii=False),
                    workflow.get("generated_from"),
                    json.dumps(workflow.get("inserted_steps", []), ensure_ascii=False),
                    workflow.get("output_path"),
                ),
            )

        for stage in payload["stages"]:
            conn.execute(
                "INSERT INTO stages VALUES (?, ?, ?, ?, ?, ?)",
                (
                    stage["stage_id"],
                    stage["title"],
                    stage["status"],
                    stage["report_path"],
                    stage["report_size"],
                    stage["updated_at"],
                ),
            )

        for event in payload["repair_events"]["events"]:
            conn.execute(
                """
                INSERT INTO repair_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["repair_id"],
                    event["event_status"],
                    event["failure_link_status"],
                    event["source_workflow_id"],
                    event.get("failure_run_id"),
                    event.get("failure_ended_at"),
                    event.get("failed_step"),
                    json.dumps(event.get("missing_fields", []), ensure_ascii=False),
                    json.dumps(event.get("suggestions", []), ensure_ascii=False),
                    event["strategy"],
                    event["generated_workflow_id"],
                    event.get("generated_workflow_path"),
                    json.dumps(event.get("inserted_steps", []), ensure_ascii=False),
                    event.get("verification_run_id"),
                    event.get("verification_status"),
                    event.get("verification_ended_at"),
                    event.get("verification_duration_ms"),
                    event.get("event_latency_ms"),
                ),
            )

        graph = payload["capability_graph"]
        for metacode_id, node in graph["nodes"].items():
            conn.execute(
                "INSERT INTO metacodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    metacode_id,
                    node.get("category"),
                    build_registry(root)[metacode_id].get("purpose", ""),
                    json.dumps(node.get("reads", []), ensure_ascii=False),
                    json.dumps(node.get("writes", []), ensure_ascii=False),
                    node.get("usage", 0),
                    node.get("in_degree", 0),
                    node.get("out_degree", 0),
                    node.get("bridge_score", 0),
                ),
            )

        for edge in graph["edges"]:
            conn.execute(
                """
                INSERT INTO graph_edges (from_id, to_id, field, from_category, to_category)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    edge["from"],
                    edge["to"],
                    edge["field"],
                    edge["from_category"],
                    edge["to_category"],
                ),
            )

        for key in (
            "dashboard_summary",
            "repair_metrics",
            "repair_events",
            "reuse_summary",
            "capability_graph_summary",
        ):
            conn.execute(
                "INSERT INTO summaries VALUES (?, ?)",
                (key, json.dumps(payload[key], ensure_ascii=False)),
            )

        conn.commit()
    finally:
        conn.close()
    return db_path


def export_monitoring_data(root: Path) -> dict[str, Any]:
    monitoring_dir = root / "monitoring"
    exports_dir = monitoring_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    (monitoring_dir / "stages").mkdir(parents=True, exist_ok=True)

    reuse_summary = analyze_reuse(root)
    graph = build_capability_graph(root)
    graph_summary = summarize_graph(root)
    runs = collect_runs(root)
    failures = [run for run in runs if run["status"] == "failed"]
    stages = collect_stage_reports(root)
    workflows = collect_workflows(root)
    repair_metrics = build_repair_metrics(runs, workflows)
    repair_events = build_repair_events(runs, workflows)
    summary = dashboard_summary(reuse_summary, graph_summary, runs, stages, workflows)
    summary["repair_attempt_count"] = repair_metrics["summary"]["attempt_count"]
    summary["repair_success_count"] = repair_metrics["summary"]["success_count"]
    summary["repair_success_rate"] = repair_metrics["summary"]["repair_success_rate"]
    summary["repair_event_count"] = repair_events["summary"]["event_count"]
    summary["repair_event_link_rate"] = repair_events["summary"]["failure_link_rate"]

    payload = {
        "dashboard_summary": summary,
        "runs": runs,
        "failures": failures,
        "stages": stages,
        "workflows": workflows,
        "repair_metrics": repair_metrics,
        "repair_events": repair_events,
        "reuse_summary": reuse_summary,
        "capability_graph": graph,
        "capability_graph_summary": graph_summary,
    }

    write_json(exports_dir / "dashboard_summary.json", summary)
    write_json(exports_dir / "runs.json", runs)
    write_json(exports_dir / "failures.json", failures)
    write_json(exports_dir / "stages.json", stages)
    write_json(exports_dir / "workflow_graph.json", workflows)
    write_json(exports_dir / "repair_metrics.json", repair_metrics)
    write_json(exports_dir / "repair_events.json", repair_events)
    write_json(exports_dir / "reuse_summary.json", reuse_summary)
    write_json(exports_dir / "capability_graph.json", graph)
    write_json(exports_dir / "capability_graph_summary.json", graph_summary)

    for stage in stages:
        write_json(monitoring_dir / "stages" / f"stage_{stage['stage_id']}.json", stage)

    db_path = write_sqlite_database(root, payload)
    payload["database_path"] = str(db_path)
    return payload
