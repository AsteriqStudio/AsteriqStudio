#!/usr/bin/env python3
"""No-render planning and quality gates for direct 3D films."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from character_library import has_saved_mesh, load_character
from visual_styles import style_contract


LIBRARY = Path(__file__).resolve().parent / "library"


def build(job: dict) -> dict:
    errors: list[str] = []
    character = job.get("character", {})
    for field in ("id", "design_brief", "height_cm", "body_proportions", "asset_version_id"):
        if not character.get(field): errors.append(f"character.{field} is required")
    if not isinstance(character.get("height_cm"), (int, float)) or not 50 <= character.get("height_cm", 0) <= 260:
        errors.append("character.height_cm must be a plausible centimetre value")
    for gate in ("turntable_approved", "rig_approved", "clothing_approved"):
        if character.get(gate) is not True: errors.append(f"character.{gate} must be approved")
    style = style_contract(str(character.get("source_style") or ""))
    if style is None:
        errors.append("character.source_style must be a known Asteriq style")
    elif style["requires_owner_opt_in"] and job.get("photorealism_owner_opt_in") is not True:
        errors.append("photorealistic 3D requires explicit owner opt-in")
    if character.get("anchor_approved") is not True or character.get("orientation") != "upright":
        errors.append("3D must be built from an approved upright style sheet, not a sideways or failed frame")
    scene = job.get("scene", {})
    for field in ("virtual_set_version_id", "camera_plan_id", "lighting_plan_id", "shot_list_id"):
        if not scene.get(field): errors.append(f"scene.{field} is required")
    if job.get("output", {}).get("resolution") == "4k" and not job["output"].get("approved_hd_edit_id"):
        errors.append("4K needs an approved HD edit")
    library = Path(job["library"]) if job.get("library") else LIBRARY
    saved = load_character(library, str(character.get("asset_version_id") or ""))
    if saved and saved.get("source_style") not in {None, character.get("source_style")}:
        errors.append("saved character style does not match this job")
    reuse_mesh = has_saved_mesh(saved)
    if reuse_mesh:
        stages = ["load saved character", "Blender motion blocking", "virtual set, props, camera and lighting", "HD render", "approved 4K finish"]
    else:
        stages = ["TRELLIS once from the approved upright sheet", "save versioned mesh, materials, textures, skeleton and blend", "topology and rig repair", "Blender motion blocking", "virtual set, props, camera and lighting", "HD render", "approved 4K finish"]
    return {
        "ready": not errors,
        "no_render": True,
        "errors": errors,
        "ordered_stages": stages,
        "saved_character": {
            "asset_version_id": character.get("asset_version_id"),
            "reusable": True,
            "loaded_from_library": saved is not None,
            "regenerate_mesh": not reuse_mesh,
        },
        "visual_style": style,
        "policy": "build the mesh once from an approved upright sheet, then reuse that saved character",
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
