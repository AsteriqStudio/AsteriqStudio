#!/usr/bin/env python3
"""Save one approved character and load it on later 3D jobs."""
from __future__ import annotations

import json
from pathlib import Path


PACKAGE_SLOTS = ("mesh", "materials", "textures", "skeleton", "blend")


def library_dir(root: Path) -> Path:
    path = root / "characters"
    path.mkdir(parents=True, exist_ok=True)
    return path


def character_path(root: Path, asset_version_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in asset_version_id)
    return library_dir(root) / f"{safe}.json"


def save_character(root: Path, record: dict) -> Path:
    asset_id = str(record.get("asset_version_id") or "")
    if not asset_id:
        raise ValueError("asset_version_id is required")
    if record.get("orientation") != "upright":
        raise ValueError("only an upright approved sheet can be saved as a reusable character")
    if record.get("anchor_approved") is not True:
        raise ValueError("the style sheet must pass review before the character is saved")
    package = {slot: (record.get("package") or {}).get(slot) for slot in PACKAGE_SLOTS}
    stored = {
        "asset_version_id": asset_id,
        "character_id": record.get("character_id"),
        "source_style": record.get("source_style"),
        "source_anchor": record.get("source_anchor"),
        "orientation": "upright",
        "anchor_approved": True,
        "reusable": True,
        "package": package,
        "status": "saved_mesh" if package.get("blend") else "anchor_approved_awaiting_first_mesh",
    }
    path = character_path(root, asset_id)
    path.write_text(json.dumps(stored, indent=2) + "\n", encoding="utf-8")
    return path


def load_character(root: Path, asset_version_id: str) -> dict | None:
    path = character_path(root, asset_version_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def has_saved_mesh(record: dict | None) -> bool:
    return bool(record and record.get("reusable") and (record.get("package") or {}).get("blend"))
