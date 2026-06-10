from __future__ import annotations

from typing import Any

from core.context import has_path


def suggest_for_missing_fields(
    registry: dict[str, dict[str, Any]],
    context: dict[str, Any],
    missing_fields: list[str],
    exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    exclude_ids = exclude_ids or set()
    missing_set = set(missing_fields)
    suggestions: list[dict[str, Any]] = []

    for metacode_id, identity in registry.items():
        if metacode_id in exclude_ids:
            continue

        writes = set(identity.get("context_write", []))
        provides = sorted(missing_set & writes)
        if not provides:
            continue

        reads = identity.get("context_read", [])
        unmet_inputs = sorted(field for field in reads if not has_path(context, field))
        score = len(provides) * 10 - len(unmet_inputs)
        suggestions.append(
            {
                "metacode_id": metacode_id,
                "name": identity.get("name", metacode_id),
                "category": identity.get("category", ""),
                "provides": provides,
                "requires": reads,
                "unmet_inputs": unmet_inputs,
                "ready": not unmet_inputs,
                "score": score,
            }
        )

    return sorted(
        suggestions,
        key=lambda item: (
            not item["ready"],
            -item["score"],
            item["metacode_id"],
        ),
    )


def format_suggestions(suggestions: list[dict[str, Any]]) -> str:
    if not suggestions:
        return "no candidate metacode found"

    parts = []
    for item in suggestions:
        status = "ready" if item["ready"] else "needs " + ", ".join(item["unmet_inputs"])
        parts.append(
            f"{item['metacode_id']} provides {', '.join(item['provides'])} ({status})"
        )
    return "; ".join(parts)
