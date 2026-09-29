#!/usr/bin/env python3
"""Style directions for anime and the other Asteriq looks."""
from __future__ import annotations

import json
from pathlib import Path


CATALOG = Path(__file__).with_name("visual-styles.json")
if not CATALOG.is_file():
    CATALOG = Path("/opt/asteriq/visual-styles.json")


def load_catalog(path: Path | None = None) -> dict:
    return json.loads((path or CATALOG).read_text(encoding="utf-8"))


def style_contract(style: str, path: Path | None = None) -> dict | None:
    catalog = load_catalog(path)
    item = catalog["styles"].get(style)
    if item is None:
        return None
    negative = ", ".join(part for part in (catalog["shared_negative"], item.get("negative", "")) if part)
    return {
        "id": style,
        "positive": item["positive"],
        "negative": negative,
        "requires_owner_opt_in": item.get("requires_owner_opt_in") is True,
        "upright": True,
    }


def missing_styles(presets: list[str], path: Path | None = None) -> list[str]:
    catalog = load_catalog(path)
    return [preset for preset in presets if preset not in catalog["styles"]]
