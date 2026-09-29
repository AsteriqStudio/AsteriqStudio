#!/usr/bin/env python3
"""Anime must stay upright, every other style is defined, and the 3D asset is reusable."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from character_library import has_saved_mesh, load_character, save_character  # noqa: E402
from proof_quality import inspect_frame  # noqa: E402
from visual_styles import missing_styles, style_contract  # noqa: E402


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fixtures" / "wardrobe-source-frame.png"
SIDEWAYS = ROOT / "fixtures" / "sideways-failure.png"
STACK = ROOT / "production-stack.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load_direct_3d():
    spec = importlib.util.spec_from_file_location("direct_3d_stage", ROOT / "direct-3d-stage.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.build


def main() -> int:
    upright = inspect_frame(SOURCE)
    if not upright["passed"] or upright["sideways_subject"]:
        fail(f"upright anime sheet was rejected: {upright}")
    sideways = inspect_frame(SIDEWAYS)
    if sideways["passed"] or not sideways["sideways_subject"]:
        fail(f"sideways frame was accepted: {sideways}")

    presets = json.loads(STACK.read_text(encoding="utf-8"))["visual_style_policy"]["presets"]
    missing = missing_styles(presets)
    if missing:
        fail(f"styles have no direction: {missing}")
    for preset in presets:
        contract = style_contract(preset)
        if contract is None or "upright" not in contract["positive"] or "sideways" not in contract["negative"]:
            fail(f"{preset} does not lock an upright result")

    build = load_direct_3d()
    job = json.loads((ROOT / "examples" / "direct-3d-job.json").read_text(encoding="utf-8"))
    first = build(job)
    if not first["ready"] or first["saved_character"]["regenerate_mesh"] is not True:
        fail(f"first 3D pass should save a mesh once: {first}")
    if "save versioned mesh" not in " ".join(first["ordered_stages"]):
        fail(f"first pass does not save the character: {first}")

    with tempfile.TemporaryDirectory() as folder_name:
        library = Path(folder_name)
        save_character(library, {
            "asset_version_id": "character-ian-v1-anime-3d",
            "character_id": "character-ian-v1",
            "source_style": "anime_illustration",
            "source_anchor": str(SOURCE),
            "orientation": "upright",
            "anchor_approved": True,
            "package": {"blend": "characters/character-ian-v1-anime-3d.blend"},
        })
        stored = load_character(library, "character-ian-v1-anime-3d")
        if not has_saved_mesh(stored):
            fail(f"saved mesh was not reusable: {stored}")
        reused = build({**job, "library": str(library)})
        if reused["saved_character"]["regenerate_mesh"] or reused["ordered_stages"][0] != "load saved character":
            fail(f"saved character was rebuilt: {reused}")
        try:
            save_character(library, {"asset_version_id": "bad", "orientation": "sideways", "anchor_approved": True})
        except ValueError:
            pass
        else:
            fail("a sideways sheet was saved as a character")

    rejected = build({**job, "character": {**job["character"], "orientation": "sideways", "anchor_approved": False}})
    if rejected["ready"]:
        fail("a sideways sheet was allowed to become 3D")
    print(json.dumps({"anime_axis": upright["subject_axis_degrees"], "sideways_axis": sideways["subject_axis_degrees"], "styles": presets}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
