#!/usr/bin/env python3
"""Record the shared Serverless volume inventory without deleting anything."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil


VOLUME = Path(os.environ.get("ASTERIQ_VOLUME_ROOT", "/runpod-volume"))
MODELS = VOLUME / "models"
REPORT = MODELS / "asteriq" / "network-volume-audit.json"


def tree_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    entries = []
    for entry in sorted(VOLUME.iterdir(), key=lambda item: item.name.lower()):
        entries.append({"name": entry.name, "kind": "directory" if entry.is_dir() else "file", "bytes": tree_bytes(entry)})
    usage = shutil.disk_usage(VOLUME)
    report = {
        "policy": "inventory_only_no_deletion",
        "volume_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "top_level_entries": entries,
        "deletion_rule": "Only explicitly identified stale Asteriq cache artifacts may be removed after review. Never delete source media, Projects, character assets, or unknown files.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Asteriq network-volume audit: {json.dumps(report)}", flush=True)


if __name__ == "__main__":
    main()
