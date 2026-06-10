from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_context(inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "inputs": deepcopy(inputs or {}),
        "data": {},
        "artifacts": {},
        "logs": [],
        "errors": [],
    }


def read_path(context: dict[str, Any], dotted_path: str) -> Any:
    current: Any = context
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def write_path(context: dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    current = context
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def has_path(context: dict[str, Any], dotted_path: str) -> bool:
    try:
        read_path(context, dotted_path)
    except KeyError:
        return False
    return True


def available_paths(context: dict[str, Any]) -> list[str]:
    paths: list[str] = []

    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_prefix = f"{prefix}.{key}" if prefix else key
                walk(child_prefix, child)
        else:
            paths.append(prefix)

    walk("", context)
    return sorted(paths)


def append_log(context: dict[str, Any], message: str, **fields: Any) -> None:
    context["logs"].append({"time": now_iso(), "message": message, **fields})


def append_error(context: dict[str, Any], message: str, **fields: Any) -> None:
    context["errors"].append({"time": now_iso(), "message": message, **fields})
