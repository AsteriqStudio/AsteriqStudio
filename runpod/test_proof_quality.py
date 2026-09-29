#!/usr/bin/env python3
"""Regression checks for the failed blue ghosted proof and starter anchors."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageFilter

from proof_quality import inspect_anchor, inspect_frame


def _load_controller():
    path = Path(__file__).resolve().parent / "production-controller.py"
    spec = importlib.util.spec_from_file_location("production_controller", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build_plan = _load_controller().build_plan


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "fixtures" / "wardrobe-source-frame.png"
EXAMPLE = ROOT / "examples" / "one-minute-source-video-job.json"
WORKFLOW = ROOT.parent / "workflows" / "video" / "wan_vace_source_video_api.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def blue_ghost(source: Image.Image) -> Image.Image:
    small = source.resize((80, 80))
    ghost = small.resize(source.size, Image.Resampling.BILINEAR)
    red, green, blue = ghost.split()
    red = red.point(lambda value: int(value * 0.25))
    green = green.point(lambda value: int(value * 0.35))
    blue = blue.point(lambda value: min(255, int(value * 0.3 + 180)))
    return Image.merge("RGB", (red, green, blue)).filter(ImageFilter.GaussianBlur(8))


def blocky_starter(source: Image.Image) -> Image.Image:
    width, height = source.size
    small = source.resize((24, max(1, round(height * 24 / width))), Image.Resampling.BOX)
    return small.resize(source.size, Image.Resampling.NEAREST)


def example_job() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def main() -> int:
    if not SOURCE.is_file():
        fail(f"missing local source frame: {SOURCE}")
    source_report = inspect_frame(SOURCE)
    if not source_report["passed"] or source_report["blue_channel_collapse"] or source_report["severe_ghosting"]:
        fail(f"wardrobe source frame was rejected: {source_report}")
    source_anchor = inspect_anchor(SOURCE, {"approval": "production", "origin": "source_frame"})
    if not source_anchor["anchor_ready"]:
        fail(f"wardrobe source frame is not an acceptable production anchor: {source_anchor}")

    with tempfile.TemporaryDirectory() as folder_name:
        folder = Path(folder_name)
        source = Image.open(SOURCE).convert("RGB")
        ghost_path = folder / "failed-proof.png"
        block_path = folder / "starter.png"
        blue_ghost(source).save(ghost_path)
        blocky_starter(source).save(block_path)

        ghost_report = inspect_frame(ghost_path)
        if not ghost_report["blue_channel_collapse"] or not ghost_report["severe_ghosting"] or ghost_report["passed"]:
            fail(f"blue ghosted proof was not rejected: {ghost_report}")

        starter = inspect_anchor(block_path, {"approval": "production", "origin": "starter_glb_preview"})
        if starter["anchor_ready"] or "starter GLB preview cannot be used as a paid-animation reference" not in starter["reasons"]:
            fail(f"starter GLB preview was accepted: {starter}")
        if "character anchor is a low-detail starter preview" not in starter["reasons"]:
            fail(f"blocky starter was not detected visually: {starter}")

        job = example_job()
        planned = build_plan(job)
        if not planned["ready"] or planned["proof_status"] != "not_submitted":
            fail(f"production anchor plan should stay ready until a proof exists: {planned}")
        audio = next(stage for stage in planned["stages"] if stage["id"] == "audio")
        if audio["authorized"] or not audio["requires_passed_proof"]:
            fail(f"audio must stay blocked until a proof passes: {audio}")

        failed = example_job()
        failed["rendered_proof"] = {"mp4_present": True, "frame_path": str(ghost_path)}
        failed_plan = build_plan(failed)
        if failed_plan.get("proof_status") != "failed" or failed_plan.get("render_submission_allowed"):
            fail(f"failed proof was treated as deliverable: {failed_plan}")
        if failed_plan.get("blocked_stages") != ["audio", "assemble", "remaining_sections"]:
            fail(f"failed proof did not block the remaining sections: {failed_plan}")
        if any(stage.get("id") == "audio" for stage in failed_plan.get("stages", [])):
            fail("failed proof still scheduled audio")

        starter_job = example_job()
        starter_job["character_anchor"] = {
            "asset_id": "starter",
            "approval": "production",
            "origin": "starter_glb_preview",
            "frame_path": str(block_path),
        }
        starter_plan = build_plan(starter_job)
        if starter_plan["ready"] or not any("starter GLB preview" in error for error in starter_plan["errors"]):
            fail(f"starter anchor reached a paid plan: {starter_plan}")

        mp4_only = example_job()
        mp4_only["rendered_proof"] = {"mp4_present": True}
        mp4_plan = build_plan(mp4_only)
        if mp4_plan["ready"] or not any("MP4 alone" in error for error in mp4_plan["errors"]):
            fail(f"MP4-only completion was accepted: {mp4_plan}")

        passed = example_job()
        passed["operator_render_approval"] = "approved"
        passed["rendered_proof"] = {"frame_path": str(SOURCE)}
        passed_plan = build_plan(passed)
        if not passed_plan["ready"] or passed_plan["proof_status"] != "passed":
            fail(f"wardrobe source proof should pass: {passed_plan}")
        passed_audio = next(stage for stage in passed_plan["stages"] if stage["id"] == "audio")
        if not passed_audio["authorized"]:
            fail(f"a passed proof should authorize audio: {passed_audio}")

    workflow_check = subprocess.run(
        [sys.executable, str(ROOT / "validate-wan-source-workflow.py"), "--workflow", str(WORKFLOW)],
        check=False,
        capture_output=True,
        text=True,
    )
    if workflow_check.returncode != 0:
        fail(workflow_check.stdout + workflow_check.stderr)
    print(json.dumps({"source_frame": source_report, "workflow_ready": True}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
