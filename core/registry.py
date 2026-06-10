from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from core.schema import validate_identity


def load_identity(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        identity = yaml.safe_load(handle) or {}
    validate_identity(identity, str(path))
    identity["_identity_path"] = str(path)
    identity["_base_dir"] = str(path.parent)
    return identity


def scan_metacodes(root: Path) -> dict[str, dict[str, Any]]:
    identities: dict[str, dict[str, Any]] = {}
    for identity_path in sorted(root.glob("metacodes/**/identity.yaml")):
        identity = load_identity(identity_path)
        metacode_id = identity["id"]
        if metacode_id in identities:
            raise ValueError(f"duplicate metacode id: {metacode_id}")
        identities[metacode_id] = identity
    return identities


def write_registry(root: Path, identities: dict[str, dict[str, Any]]) -> Path:
    registry_dir = root / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_path = registry_dir / "metacodes.json"
    with registry_path.open("w", encoding="utf-8") as handle:
        json.dump(identities, handle, ensure_ascii=False, indent=2)
    return registry_path


def build_registry(root: Path) -> dict[str, dict[str, Any]]:
    identities = scan_metacodes(root)
    write_registry(root, identities)
    return identities
