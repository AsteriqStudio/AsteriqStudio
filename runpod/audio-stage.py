#!/usr/bin/env python3
"""No-render validation for a consistent, consent-backed audio/subtitle stage."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def fingerprint(profile: dict) -> str:
    public_fields = {key: profile.get(key) for key in ("character_version_id", "locked_profile_id", "presentation", "style", "treatment", "pitch_shift", "formant_shift", "tone_color_seed", "voice_direction")}
    return hashlib.sha256(json.dumps(public_fields, sort_keys=True).encode()).hexdigest()[:16]


def build(job: dict) -> dict:
    errors: list[str] = []
    profiles = job.get("profiles", [])
    if not profiles:
        errors.append("at least one character voice profile is required")
    ids: set[str] = set()
    prints: set[str] = set()
    for profile in profiles:
        pid = profile.get("character_version_id", "unnamed")
        if profile.get("reference_voice_uri") and profile.get("reference_voice_consent") is not True: errors.append(f"{pid}: a real reference voice requires consent")
        if not profile.get("locked_profile_id"): errors.append(f"{pid}: locked_profile_id is required")
        if pid in ids: errors.append(f"{pid}: character appears more than once")
        ids.add(pid)
        value = fingerprint(profile)
        if value in prints: errors.append(f"{pid}: voice settings duplicate another character")
        prints.add(value)
    subtitles = job.get("subtitles", {})
    if subtitles.get("languages") != ["en", "de"]: errors.append("English and German subtitles are required")
    if subtitles.get("style") not in {"yellow_no_box", "black_outline_no_box"}: errors.append("subtitle style must be legible and have no background box")
    if not job.get("series_continuity_snapshot_id"): errors.append("series continuity snapshot is required")
    if job.get("background_policy") != "suppress_room_and_background_voices":
        errors.append("background and room voices must be removed from the mix")
    if job.get("voice_policy") != "alter_locked_profile":
        errors.append("the locked character voice must be altered; the source soundtrack cannot be copied")
    dialogue = str(job.get("dialogue") or "").strip()
    lip_sync = job.get("lip_sync") or {}
    if dialogue and lip_sync.get("required") is not True: errors.append("dialogue requires lip-sync")
    if dialogue and lip_sync.get("quality_gate") != "phoneme_timing_matches_final_waveform": errors.append("lip-sync must validate the final waveform")
    return {
        "ready": not errors,
        "no_render": True,
        "errors": errors,
        "profile_fingerprints": sorted(prints),
        "output": ["character dialogue WAV", "lip-synced video", "timed transcript", "en.vtt", "de.vtt", "en.ass", "de.ass", "captioned master MP4"],
        "ordered_pipeline": ["synthesize_or_convert", "freeze waveform", "LatentSync 1.6", "ASR", "translation", "subtitle export", "overlay and mux"],
        "policy": "freeze every approved profile into the series continuity snapshot; use the same profile only for the same character",
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
