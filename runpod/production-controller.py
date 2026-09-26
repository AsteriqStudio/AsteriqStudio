#!/usr/bin/env python3
"""Build fail-closed, no-render production jobs for Asteriq Serverless.

This controller is deliberately a planning boundary.  It creates the ordered
stage graph a RunPod client submits only after the caller gives an explicit
render approval.  It never invokes ComfyUI, Blender, OpenVoice, FFmpeg, or a
RunPod endpoint itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


FPS = 24
SECTION_SECONDS = 10
UNIQUE_SECTION_FRAMES = FPS * SECTION_SECONDS
HANDOFF_FRAMES = FPS
ALLOWED_DURATIONS = {60, 300, 600}
SUPPORTED_URI_PREFIXES = ("s3://", "https://", "http://")


def fail(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def stable_id(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def plan_sections(duration: int, continuity_snapshot: str) -> list[dict[str, Any]]:
    count = duration // SECTION_SECONDS
    sections: list[dict[str, Any]] = []
    for index in range(count):
        section_id = f"section-{index + 1:03d}"
        sections.append({
            "id": section_id,
            "start_frame": index * UNIQUE_SECTION_FRAMES,
            "unique_output_frames": UNIQUE_SECTION_FRAMES,
            "internal_generation_frames": UNIQUE_SECTION_FRAMES + HANDOFF_FRAMES,
            "predecessor": None if index == 0 else f"section-{index:03d}",
            "handoff_input_frames": 0 if index == 0 else HANDOFF_FRAMES,
            "continuity_snapshot_id": continuity_snapshot,
            "boundary_quality_gate": [] if index == 0 else [
                "pose_and_mask_continuity",
                "character_anchor_similarity",
                "camera_motion_continuity",
                "lighting_and_exposure_continuity",
                "constant_24fps_cadence",
            ],
        })
    return sections


def validate(job: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    duration = job.get("duration_seconds")
    fail(errors, duration in ALLOWED_DURATIONS, "duration_seconds must be 60, 300, or 600")
    source = job.get("source", {})
    uri = source.get("video_uri")
    fail(errors, isinstance(uri, str) and uri.startswith(SUPPORTED_URI_PREFIXES), "source.video_uri must be a signed HTTPS URL or s3:// object URI")
    fail(errors, source.get("fps") == FPS and source.get("constant_frame_rate") is True, "source must be conformed to constant 24 fps")
    fail(errors, bool(source.get("content_hash")), "source.content_hash is required to reuse unchanged tracking safely")
    cast = source.get("performers", [])
    fail(errors, bool(cast), "each visible performer must have a cast assignment")
    characters: set[str] = set()
    voices: set[str] = set()
    for performer in cast:
        label = performer.get("id", "unnamed performer")
        character = performer.get("character_version_id")
        voice = performer.get("voice_profile_id")
        fail(errors, bool(character), f"{label}: missing character_version_id")
        fail(errors, bool(voice), f"{label}: missing voice_profile_id")
        fail(errors, performer.get("voice_consent") is True, f"{label}: voice profile lacks consent confirmation")
        fail(errors, performer.get("track_seed") is not None, f"{label}: missing deterministic track_seed")
        if character:
            fail(errors, character not in characters, f"{label}: character version is assigned twice")
            characters.add(character)
        if voice:
            fail(errors, voice not in voices, f"{label}: voice profile is assigned twice")
            voices.add(voice)
    continuity = job.get("continuity", {})
    for field in ("cast_snapshot_id", "wardrobe_snapshot_id", "virtual_set_version_id", "camera_plan_id", "lighting_plan_id", "style_seed_map_id"):
        fail(errors, bool(continuity.get(field)), f"continuity.{field} is required")
    output = job.get("output", {})
    fail(errors, output.get("container") == "mp4", "output.container must be mp4")
    fail(errors, output.get("subtitle_languages") == ["en", "de"], "English and German subtitle tracks are required")
    if output.get("resolution") == "4k":
        fail(errors, bool(output.get("approved_hd_edit_id")), "4K requires an approved HD edit")
    quote = job.get("gpu_quote", {})
    rate = quote.get("usd_per_hour")
    estimate = quote.get("estimated_gpu_seconds")
    budget = job.get("budget", {})
    fail(errors, isinstance(rate, (int, float)) and rate > 0, "fresh worker hourly quote is required")
    fail(errors, isinstance(estimate, int) and estimate > 0, "estimated_gpu_seconds is required")
    fail(errors, isinstance(budget.get("max_usd"), (int, float)) and budget["max_usd"] > 0, "budget.max_usd is required")
    if isinstance(rate, (int, float)) and isinstance(estimate, int) and isinstance(budget.get("max_usd"), (int, float)):
        fail(errors, (rate * estimate / 3600) <= budget["max_usd"], "estimate exceeds the per-video cost ceiling")
    fail(errors, job.get("cache_readiness") == "ready", "shared model cache must report ready")
    return errors


def build_plan(job: dict[str, Any]) -> dict[str, Any]:
    errors = validate(job)
    if errors:
        return {"ready": False, "no_render": True, "errors": errors}
    continuity_id = stable_id(job["continuity"])
    sections = plan_sections(job["duration_seconds"], continuity_id)
    changed = set(job.get("changed_section_ids", []))
    unknown = changed - {section["id"] for section in sections}
    if unknown:
        return {"ready": False, "no_render": True, "errors": [f"unknown changed sections: {', '.join(sorted(unknown))}"]}
    rerender = set(changed)
    # Each edit is checked together with the following handoff.  The first
    # section has no predecessor; a change in a later section also validates
    # the prior section's tail without regenerating the entire film.
    for section in sections:
        if section["id"] in changed and section["predecessor"]:
            rerender.add(section["predecessor"])
    stages = [
        {"id": "ingest", "kind": "ffmpeg_conform", "gpu": False},
        {"id": "track", "kind": "sam2_and_pose", "gpu": True},
        {"id": "render", "kind": "wan_vace_source_video", "gpu": True, "sections": sections},
        {"id": "audio", "kind": "openvoice_asr_translate_subtitles", "gpu": True},
        {"id": "assemble", "kind": "ffmpeg_cfr_mp4", "gpu": False},
    ]
    approval = job.get("operator_render_approval") == "approved"
    return {
        "ready": True,
        "no_render": not approval,
        "render_submission_allowed": approval,
        "job_id": f"asteriq-{stable_id(job)}",
        "continuity_snapshot_id": continuity_id,
        "final_timeline": {
            "fps": FPS,
            "duration_seconds": job["duration_seconds"],
            "output_frames": job["duration_seconds"] * FPS,
            "policy": "one master timeline; internal windows are temporal handoffs, never independent clips",
        },
        "stages": stages,
        "rerender_scope": "all_sections" if not changed else sorted(rerender),
        "cost_guard": {
            "quoted_usd_per_hour": job["gpu_quote"]["usd_per_hour"],
            "estimated_gpu_seconds": job["gpu_quote"]["estimated_gpu_seconds"],
            "max_usd": job["budget"]["max_usd"],
            "on_exceed": "block_submission",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("job", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_plan(json.loads(args.job.read_text(encoding="utf-8")))
    payload = json.dumps(report, indent=2)
    if args.out:
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if report.get("ready") else 78


if __name__ == "__main__":
    sys.exit(main())
