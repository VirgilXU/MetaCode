from __future__ import annotations

import json
import re
import sqlite3
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
    return stages


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
    return {
        "current_stage": max((stage["stage_id"] for stage in stages), default=None),
        "metacode_count": reuse_summary["metacode_count"],
        "stable_workflow_count": reuse_summary["workflow_count"],
        "workflow_file_count": len(workflows),
        "run_count": len(runs),
        "success_run_count": len(successes),
        "failure_run_count": len(failures),
        "edge_count": graph_summary["edge_count"],
        "field_count": graph_summary["field_count"],
        "unresolved_field_count": len(graph_summary["unresolved_fields"]),
        "latest_run": latest_run,
    }


def write_sqlite_database(root: Path, payload: dict[str, Any]) -> Path:
    monitoring_dir = root / "monitoring"
    db_path = monitoring_dir / "metacode_monitor.db"
    schema_path = monitoring_dir / "schema.sql"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        for table in ("runs", "workflows", "stages", "metacodes", "graph_edges", "summaries"):
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

        for key in ("dashboard_summary", "reuse_summary", "capability_graph_summary"):
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
    summary = dashboard_summary(reuse_summary, graph_summary, runs, stages, workflows)

    payload = {
        "dashboard_summary": summary,
        "runs": runs,
        "failures": failures,
        "stages": stages,
        "workflows": workflows,
        "reuse_summary": reuse_summary,
        "capability_graph": graph,
        "capability_graph_summary": graph_summary,
    }

    write_json(exports_dir / "dashboard_summary.json", summary)
    write_json(exports_dir / "runs.json", runs)
    write_json(exports_dir / "failures.json", failures)
    write_json(exports_dir / "stages.json", stages)
    write_json(exports_dir / "workflow_graph.json", workflows)
    write_json(exports_dir / "reuse_summary.json", reuse_summary)
    write_json(exports_dir / "capability_graph.json", graph)
    write_json(exports_dir / "capability_graph_summary.json", graph_summary)

    for stage in stages:
        write_json(monitoring_dir / "stages" / f"stage_{stage['stage_id']}.json", stage)

    db_path = write_sqlite_database(root, payload)
    payload["database_path"] = str(db_path)
    return payload
