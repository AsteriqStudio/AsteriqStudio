#!/usr/bin/env python3
"""Fail-closed, no-render preflight for an Asteriq source-video production job.

This program does not start ComfyUI, Blender, an audio model, or a RunPod job.
It checks the submitted production plan before the controller is allowed to
reserve GPU time.  A valid report is therefore safe to run against the first
uploaded video without incurring video-generation GPU cost.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path("/opt/asteriq")
MANIFEST = ROOT / "source-video-workflow-manifest.json"
STACK = ROOT / "production-stack.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path, help="JSON production plan supplied by the job controller")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--stack", type=Path, default=STACK)
    parser.add_argument("--cache-report", type=Path)
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    stack = read_json(args.stack)
    plan = read_json(args.plan)
    errors: list[str] = []
    warnings: list[str] = []

    source = plan.get("source", {})
    fail(errors, bool(source.get("video_uri")), "source.video_uri is required")
    fail(errors, source.get("fps") == manifest["timeline"]["fps"], "source must be a constant 24 fps proxy or conform job")
    fail(errors, source.get("constant_frame_rate") is True, "source must be constant-frame-rate before tracking")
    duration = plan.get("duration_seconds")
    fail(errors, duration in manifest["timeline"]["final_durations_seconds"], "duration must be one of 60, 300 or 600 seconds")

    style = plan.get("visual_style", manifest["visual_style_policy"]["default"])
    allowed = set(manifest["visual_style_policy"]["allowed_defaults"])
    photorealistic = style == "photorealistic"
    fail(errors, style in allowed or photorealistic, "visual_style is not an approved Asteriq style")
    if photorealistic:
        fail(errors, plan.get("photorealism_owner_opt_in") is True, "photorealistic output requires explicit owner opt-in")

    performers = source.get("performers", [])
    fail(errors, bool(performers), "every visible performer must be declared")
    character_ids: set[str] = set()
    voice_ids: set[str] = set()
    for performer in performers:
        pid = performer.get("id", "unnamed performer")
        character = performer.get("character_version_id")
        voice = performer.get("voice_profile_id")
        fail(errors, bool(character), f"{pid}: missing character_version_id")
        fail(errors, bool(voice), f"{pid}: missing voice_profile_id")
        fail(errors, performer.get("track_seed") is not None, f"{pid}: missing deterministic track_seed")
        if character:
            fail(errors, character not in character_ids, f"{pid}: character version is assigned to more than one performer")
            character_ids.add(character)
        if voice:
            fail(errors, voice not in voice_ids, f"{pid}: voice profile is assigned to more than one performer")
            voice_ids.add(voice)

    series = plan.get("series")
    if series:
        fail(errors, bool(series.get("id")), "series continuity requires a series id")
        fail(errors, bool(series.get("continuity_snapshot_id")), "series continuity requires a saved continuity snapshot")
    else:
        warnings.append("no series continuity snapshot: this render is treated as a standalone film")

    checkpoints = plan.get("checkpoint_seconds", manifest["timeline"]["internal_checkpoint_seconds"])
    fail(errors, checkpoints == manifest["timeline"]["internal_checkpoint_seconds"], "internal checkpoints must be 10 seconds")
    if isinstance(duration, int):
        fail(errors, duration % checkpoints == 0, "duration must divide into whole 10-second checkpoints")

    output = plan.get("output", {})
    fail(errors, output.get("container") == "mp4", "output.container must be mp4")
    fail(errors, output.get("subtitles") == ["en", "de"], "output must include English and German subtitle tracks")
    if output.get("resolution") == "4k":
        fail(errors, output.get("approved_hd_edit_id") is not None, "4K finish requires an approved HD edit")

    quote = plan.get("gpu_quote", {})
    price_guard = stack["price_guard"]
    rate = quote.get("usd_per_hour")
    fail(errors, isinstance(rate, (int, float)), "a fresh worker GPU quote is required")
    if isinstance(rate, (int, float)):
        fail(errors, rate <= price_guard["worst_case_hourly_price"], "quoted GPU rate exceeds the configured price ceiling")
    estimated = quote.get("estimated_gpu_seconds")
    if isinstance(estimated, int) and isinstance(duration, int):
        cap = stack["cost_profiles"][plan.get("cost_profile", "fast_economy")]["maximum_gpu_seconds_per_output_minute"]
        fail(errors, estimated <= cap * (duration // 60), "GPU estimate exceeds the selected per-minute ceiling")
    else:
        errors.append("estimated_gpu_seconds is required")

    report_path = args.cache_report or Path(os.environ.get("ASTERIQ_MODEL_ROOT", "/runpod-volume/models")) / "asteriq" / "model-cache-readiness.json"
    anchor = plan.get("character_anchor") or {}
    fail(errors, anchor.get("approval") == "production", "paid animation requires a production character anchor")
    origin = anchor.get("origin")
    rejected_origins = {"starter_glb_preview", "procedural_placeholder", "glb_viewport", "blocky_starter"}
    if origin in rejected_origins:
        errors.append("starter GLB preview cannot be used as a paid-animation reference")
    else:
        fail(errors, origin in {"approved_anime_sheet", "source_frame"}, "character anchor must be an approved anime sheet or the source frame")

    fail(errors, report_path.is_file(), "shared model cache readiness report is missing")
    if report_path.is_file():
        cache = read_json(report_path)
        fail(errors, cache.get("ready") is True, "shared model cache is not ready")
        missing = [artifact.get("id", "unknown") for artifact in cache.get("artifacts", []) if artifact.get("status") != "ready"]
        fail(errors, not missing, f"shared model cache has unavailable artifacts: {', '.join(missing)}")

    report = {
        "preflight_version": "source-video-v1",
        "no_render": True,
        "ready": not errors,
        "errors": errors,
        "warnings": warnings,
        "checkpoint_count": duration // checkpoints if isinstance(duration, int) and checkpoints else None,
        "policy": "do_not_submit_gpu_job_unless_ready_is_true",
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 78


if __name__ == "__main__":
    sys.exit(main())
