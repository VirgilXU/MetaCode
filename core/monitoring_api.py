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
    bundle["api"] = {
        "mode": "api",
        "version": "stage10",
        "endpoints": [
            "/api/status",
            "/api/monitoring",
            "/api/runs",
            "/api/failures",
            "/api/workflows",
            "/api/stages",
            "/api/reuse-summary",
            "/api/capability-graph",
            "/api/reports",
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
            "version": "stage10",
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
