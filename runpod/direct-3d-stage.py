#!/usr/bin/env python3
"""No-render planning and quality gates for direct 3D films."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def build(job: dict) -> dict:
    errors: list[str] = []
    character = job.get("character", {})
    for field in ("id", "design_brief", "height_cm", "body_proportions", "asset_version_id"):
        if not character.get(field): errors.append(f"character.{field} is required")
    if not isinstance(character.get("height_cm"), (int, float)) or not 50 <= character.get("height_cm", 0) <= 260:
        errors.append("character.height_cm must be a plausible centimetre value")
    for gate in ("turntable_approved", "rig_approved", "clothing_approved"):
        if character.get(gate) is not True: errors.append(f"character.{gate} must be approved")
    scene = job.get("scene", {})
    for field in ("virtual_set_version_id", "camera_plan_id", "lighting_plan_id", "shot_list_id"):
        if not scene.get(field): errors.append(f"scene.{field} is required")
    if job.get("output", {}).get("resolution") == "4k" and not job["output"].get("approved_hd_edit_id"):
        errors.append("4K needs an approved HD edit")
    return {
        "ready": not errors,
        "no_render": True,
        "errors": errors,
        "ordered_stages": ["TRELLIS 3D asset", "topology and rig repair", "Blender motion blocking", "virtual set, props, camera and lighting", "HD render", "approved 4K finish"],
        "policy": "this route renders a real 3D scene directly; it does not begin with a 2D animated video",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job", type=Path)
    args = parser.parse_args()
    report = build(json.loads(args.job.read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 78


if __name__ == "__main__":
    sys.exit(main())
