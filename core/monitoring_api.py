from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from core.monitoring_store import export_monitoring_data


EXPORT_FILES = {
    "summary": "dashboard_summary.json",
    "runs": "runs.json",
    "failures": "failures.json",
    "stages": "stages.json",
    "workflows": "workflow_graph.json",
    "repairs": "repair_metrics.json",
    "repairEvents": "repair_events.json",
    "reuse": "reuse_summary.json",
    "graph": "capability_graph.json",
    "graphSummary": "capability_graph_summary.json",
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def exports_dir(root: Path) -> Path:
    return root / "monitoring" / "exports"


def load_export(root: Path, key: str) -> Any:
    file_name = EXPORT_FILES[key]
    return read_json(exports_dir(root) / file_name)


def load_monitoring_bundle(root: Path) -> dict[str, Any]:
    bundle = {key: load_export(root, key) for key in EXPORT_FILES}
    diagnostics = with_repair_summary(build_diagnostics(bundle["failures"]), bundle["repairs"])
    bundle["diagnostics"] = diagnostics
    bundle["api"] = {
        "mode": "api",
        "version": "stage13",
        "endpoints": [
            "/api/status",
            "/api/monitoring",
            "/api/runs",
            "/api/failures",
            "/api/workflows",
            "/api/repairs/summary",
            "/api/repairs/by-strategy",
            "/api/repairs/by-workflow",
            "/api/repairs/recent",
            "/api/repair-events/summary",
            "/api/repair-events",
            "/api/repair-events/by-strategy",
            "/api/repair-events/by-workflow",
            "/api/repair-events/recent",
            "/api/stages",
            "/api/reuse-summary",
            "/api/capability-graph",
            "/api/reports",
            "/api/diagnostics/summary",
            "/api/diagnostics/by-field",
            "/api/diagnostics/by-workflow",
            "/api/diagnostics/by-metacode",
            "/api/export-monitoring-data",
        ],
    }
    return bundle


def to_int(value: str | None, default: int, minimum: int = 1, maximum: int = 1000) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(minimum, min(parsed, maximum))


def first_param(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def filter_runs(runs: list[dict[str, Any]], query: dict[str, list[str]]) -> list[dict[str, Any]]:
    status = first_param(query, "status")
    workflow_id = first_param(query, "workflow_id")
    limit = to_int(first_param(query, "limit"), default=100)
    filtered = runs
    if status:
        filtered = [run for run in filtered if run.get("status") == status]
    if workflow_id:
        filtered = [run for run in filtered if run.get("workflow_id") == workflow_id]
    return list(reversed(filtered))[:limit]


def filter_workflows(workflows: list[dict[str, Any]], query: dict[str, list[str]]) -> list[dict[str, Any]]:
    status_type = first_param(query, "type")
    if not status_type:
        return workflows
    if status_type == "generated":
        return [workflow for workflow in workflows if str(workflow.get("status_type", "")).startswith("generated")]
    return [workflow for workflow in workflows if workflow.get("status_type") == status_type]


def sorted_rows(counter: dict[str, dict[str, Any]], count_key: str = "failure_count") -> list[dict[str, Any]]:
    return sorted(counter.values(), key=lambda row: (-row[count_key], str(row.get("id") or row.get("field") or "")))


def with_repair_summary(diagnostics: dict[str, Any], repairs: dict[str, Any]) -> dict[str, Any]:
    repair_summary = repairs.get("summary", {})
    diagnostics["summary"]["repair_success_rate"] = repair_summary.get("repair_success_rate")
    diagnostics["summary"]["repair_success_rate_status"] = repair_summary.get("status", "computed")
    diagnostics["summary"]["repair_attempt_count"] = repair_summary.get("attempt_count", 0)
    diagnostics["summary"]["repair_success_count"] = repair_summary.get("success_count", 0)
    return diagnostics


def build_diagnostics(failures: list[dict[str, Any]]) -> dict[str, Any]:
    by_field: dict[str, dict[str, Any]] = {}
    by_workflow: dict[str, dict[str, Any]] = {}
    by_metacode: dict[str, dict[str, Any]] = {}
    missing_field_mentions = 0
    suggestion_count = 0
    ready_suggestion_count = 0

    for failure in failures:
        workflow_id = failure.get("workflow_id") or "unknown"
        failed_step = failure.get("failed_step") or "unknown"
        reason = failure.get("reason") or ""
        missing_fields = failure.get("missing_fields") or []
        suggestions = failure.get("suggestions") or []

        workflow_row = by_workflow.setdefault(
            workflow_id,
            {
                "id": workflow_id,
                "workflow_id": workflow_id,
                "failure_count": 0,
                "failed_steps": {},
                "missing_fields": {},
                "suggested_metacodes": {},
                "ready_suggestion_count": 0,
                "latest_reason": "",
            },
        )
        workflow_row["failure_count"] += 1
        workflow_row["failed_steps"][failed_step] = workflow_row["failed_steps"].get(failed_step, 0) + 1
        workflow_row["latest_reason"] = reason

        for field in missing_fields:
            missing_field_mentions += 1
            workflow_row["missing_fields"][field] = workflow_row["missing_fields"].get(field, 0) + 1
            field_row = by_field.setdefault(
                field,
                {
                    "field": field,
                    "failure_count": 0,
                    "workflows": {},
                    "suggested_metacodes": {},
                    "ready_suggestion_count": 0,
                    "latest_reason": "",
                },
            )
            field_row["failure_count"] += 1
            field_row["workflows"][workflow_id] = field_row["workflows"].get(workflow_id, 0) + 1
            field_row["latest_reason"] = reason

        for suggestion in suggestions:
            metacode_id = suggestion.get("metacode_id") or "unknown"
            ready = bool(suggestion.get("ready"))
            suggestion_count += 1
            if ready:
                ready_suggestion_count += 1
                workflow_row["ready_suggestion_count"] += 1

            workflow_row["suggested_metacodes"][metacode_id] = (
                workflow_row["suggested_metacodes"].get(metacode_id, 0) + 1
            )

            metacode_row = by_metacode.setdefault(
                metacode_id,
                {
                    "id": metacode_id,
                    "metacode_id": metacode_id,
                    "suggestion_count": 0,
                    "ready_count": 0,
                    "workflows": {},
                    "missing_fields": {},
                },
            )
            metacode_row["suggestion_count"] += 1
            if ready:
                metacode_row["ready_count"] += 1
            metacode_row["workflows"][workflow_id] = metacode_row["workflows"].get(workflow_id, 0) + 1
            for field in missing_fields:
                metacode_row["missing_fields"][field] = metacode_row["missing_fields"].get(field, 0) + 1
                if field in by_field:
                    by_field[field]["suggested_metacodes"][metacode_id] = (
                        by_field[field]["suggested_metacodes"].get(metacode_id, 0) + 1
                    )
                    if ready:
                        by_field[field]["ready_suggestion_count"] += 1

    field_rows = sorted_rows(by_field)
    workflow_rows = sorted_rows(by_workflow)
    metacode_rows = sorted(
        by_metacode.values(),
        key=lambda row: (-row["suggestion_count"], -row["ready_count"], row["metacode_id"]),
    )
    summary = {
        "failure_count": len(failures),
        "workflow_failure_count": len(by_workflow),
        "missing_field_mentions": missing_field_mentions,
        "unique_missing_field_count": len(by_field),
        "suggestion_count": suggestion_count,
        "ready_suggestion_count": ready_suggestion_count,
        "top_field": field_rows[0] if field_rows else None,
        "top_workflow": workflow_rows[0] if workflow_rows else None,
        "top_metacode": metacode_rows[0] if metacode_rows else None,
        "repair_success_rate": None,
        "repair_success_rate_status": "reserved",
    }
    return {
        "summary": summary,
        "by_field": field_rows,
        "by_workflow": workflow_rows,
        "by_metacode": metacode_rows,
    }


def report_rows(root: Path) -> list[dict[str, Any]]:
    stages = load_export(root, "stages")
    return [
        {
            "stage_id": stage["stage_id"],
            "title": stage["title"],
            "status": stage["status"],
            "report_name": Path(stage["report_path"]).name,
            "report_path": stage["report_path"],
            "report_size": stage["report_size"],
            "updated_at": stage["updated_at"],
        }
        for stage in stages
    ]


def api_response(root: Path, method: str, path: str, query: dict[str, list[str]]) -> tuple[int, Any]:
    if method == "GET" and path == "/api/status":
        summary = load_export(root, "summary")
        return HTTPStatus.OK, {
            "status": "ok",
            "service": "MetaCode Observatory API",
            "version": "stage13",
            "current_stage": summary.get("current_stage"),
            "last_exported_at": summary.get("last_exported_at"),
            "summary": summary,
        }

    if method == "GET" and path == "/api/monitoring":
        return HTTPStatus.OK, load_monitoring_bundle(root)

    if method == "GET" and path == "/api/runs":
        return HTTPStatus.OK, filter_runs(load_export(root, "runs"), query)

    if method == "GET" and path == "/api/failures":
        limit = to_int(first_param(query, "limit"), default=100)
        failures = load_export(root, "failures")
        return HTTPStatus.OK, list(reversed(failures))[:limit]

    if method == "GET" and path == "/api/workflows":
        return HTTPStatus.OK, filter_workflows(load_export(root, "workflows"), query)

    if method == "GET" and path == "/api/repairs/summary":
        return HTTPStatus.OK, load_export(root, "repairs")["summary"]

    if method == "GET" and path == "/api/repairs/by-strategy":
        return HTTPStatus.OK, load_export(root, "repairs")["by_strategy"]

    if method == "GET" and path == "/api/repairs/by-workflow":
        return HTTPStatus.OK, load_export(root, "repairs")["by_workflow"]

    if method == "GET" and path == "/api/repairs/recent":
        return HTTPStatus.OK, load_export(root, "repairs")["recent_attempts"]

    if method == "GET" and path == "/api/repair-events/summary":
        return HTTPStatus.OK, load_export(root, "repairEvents")["summary"]

    if method == "GET" and path == "/api/repair-events":
        limit = to_int(first_param(query, "limit"), default=100)
        events = load_export(root, "repairEvents")["events"]
        return HTTPStatus.OK, list(reversed(events))[:limit]

    if method == "GET" and path == "/api/repair-events/by-strategy":
        return HTTPStatus.OK, load_export(root, "repairEvents")["by_strategy"]

    if method == "GET" and path == "/api/repair-events/by-workflow":
        return HTTPStatus.OK, load_export(root, "repairEvents")["by_workflow"]

    if method == "GET" and path == "/api/repair-events/recent":
        return HTTPStatus.OK, load_export(root, "repairEvents")["recent_events"]

    if method == "GET" and path == "/api/stages":
        return HTTPStatus.OK, load_export(root, "stages")

    if method == "GET" and path == "/api/reuse-summary":
        return HTTPStatus.OK, load_export(root, "reuse")

    if method == "GET" and path == "/api/capability-graph":
        return HTTPStatus.OK, {
            "graph": load_export(root, "graph"),
            "summary": load_export(root, "graphSummary"),
        }

    if method == "GET" and path == "/api/reports":
        return HTTPStatus.OK, report_rows(root)

    if method == "GET" and path == "/api/diagnostics/summary":
        diagnostics = with_repair_summary(build_diagnostics(load_export(root, "failures")), load_export(root, "repairs"))
        return HTTPStatus.OK, diagnostics["summary"]

    if method == "GET" and path == "/api/diagnostics/by-field":
        return HTTPStatus.OK, build_diagnostics(load_export(root, "failures"))["by_field"]

    if method == "GET" and path == "/api/diagnostics/by-workflow":
        return HTTPStatus.OK, build_diagnostics(load_export(root, "failures"))["by_workflow"]

    if method == "GET" and path == "/api/diagnostics/by-metacode":
        return HTTPStatus.OK, build_diagnostics(load_export(root, "failures"))["by_metacode"]

    if method == "POST" and path == "/api/export-monitoring-data":
        payload = export_monitoring_data(root)
        return HTTPStatus.OK, {
            "status": "exported",
            "database_path": payload["database_path"],
            "run_count": len(payload["runs"]),
            "stage_count": len(payload["stages"]),
            "workflow_count": len(payload["workflows"]),
            "summary": payload["dashboard_summary"],
        }

    return HTTPStatus.NOT_FOUND, {
        "status": "not_found",
        "path": path,
    }


def create_handler(root: Path) -> type[SimpleHTTPRequestHandler]:
    project_root = root.resolve()

    class MetaCodeApiHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(project_root), **kwargs)

        def end_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            super().end_headers()

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self.handle_api("GET", parsed.path, parse_qs(parsed.query))
                return
            super().do_GET()

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                length = int(self.headers.get("Content-Length", "0"))
                if length:
                    self.rfile.read(length)
                self.handle_api("POST", parsed.path, parse_qs(parsed.query))
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def handle_api(self, method: str, path: str, query: dict[str, list[str]]) -> None:
            try:
                status, payload = api_response(project_root, method, path, query)
            except FileNotFoundError as error:
                status, payload = HTTPStatus.SERVICE_UNAVAILABLE, {
                    "status": "missing_export",
                    "message": str(error),
                }
            except Exception as error:  # pragma: no cover - defensive HTTP boundary
                status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {
                    "status": "error",
                    "message": str(error),
                }
            body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return MetaCodeApiHandler


def serve(root: Path, host: str = "127.0.0.1", port: int = 8770) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), create_handler(root))
    return server
