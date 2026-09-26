#!/usr/bin/env python3
"""No-render validation for a consistent, consent-backed audio/subtitle stage."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def fingerprint(profile: dict) -> str:
    public_fields = {key: profile.get(key) for key in ("presentation", "treatment", "pitch_shift", "tempo", "tone_color_seed")}
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
        if not profile.get("consent"): errors.append(f"{pid}: consent is required")
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
    return {
        "ready": not errors,
        "no_render": True,
        "errors": errors,
        "profile_fingerprints": sorted(prints),
        "output": ["converted dialogue WAV", "timed transcript", "en.vtt", "de.vtt", "en.ass", "de.ass"],
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
