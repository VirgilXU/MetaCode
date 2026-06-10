from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = {
    "id": str,
    "name": str,
    "version": str,
    "language": str,
    "category": str,
    "purpose": str,
    "context_read": list,
    "context_write": list,
    "runner": str,
}


def validate_identity(identity: dict[str, Any], source: str = "<memory>") -> None:
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in identity:
            raise ValueError(f"{source}: missing required field '{field}'")
        if not isinstance(identity[field], expected_type):
            actual = type(identity[field]).__name__
            expected = expected_type.__name__
            raise ValueError(f"{source}: field '{field}' must be {expected}, got {actual}")

    for field in ("context_read", "context_write"):
        for item in identity[field]:
            if not isinstance(item, str) or "." not in item:
                raise ValueError(f"{source}: {field} item must be a dotted path, got {item!r}")
