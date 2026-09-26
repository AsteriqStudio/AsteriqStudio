#!/usr/bin/env python3
"""Create a no-render, deterministic plan for an Asteriq long-form timeline."""
from __future__ import annotations

import argparse
import json
import sys

FPS = 24
SECTION_SECONDS = 10
UNIQUE_FRAMES = FPS * SECTION_SECONDS
HANDOFF_FRAMES = FPS
ALLOWED_DURATIONS = (60, 300, 600)


def make_plan(duration: int) -> dict:
    if duration not in ALLOWED_DURATIONS:
        raise ValueError("duration must be one of 60, 300, or 600 seconds")
    count = duration // SECTION_SECONDS
    sections = []
    for index in range(count):
        sections.append({
            "id": f"section-{index + 1:03d}",
            "timeline_start_frame": index * UNIQUE_FRAMES,
            "output_unique_frames": UNIQUE_FRAMES,
            "internal_generation_frames": UNIQUE_FRAMES + HANDOFF_FRAMES,
            "handoff_input_frames": HANDOFF_FRAMES if index else 0,
            "depends_on": None if index == 0 else f"section-{index:03d}",
            "continuity_snapshot": ["cast_versions", "wardrobe_versions", "virtual_set_version", "camera_plan", "lighting_plan", "style_seed_map"],
            "boundary_gate": None if index == 0 else ["pose_mask_match", "character_anchor_match", "motion_vector_match", "color_exposure_match", "constant_24fps"],
        })
    output_frames = duration * FPS
    assert sum(section["output_unique_frames"] for section in sections) == output_frames
    return {
        "ready": True,
        "policy": "one master timeline; temporally conditioned internal sections; no independent clip concatenation",
        "duration_seconds": duration,
        "fps": FPS,
        "expected_output_frames": output_frames,
        "sections": sections,
        "assembly": {
            "cfr": True,
            "final_duration_seconds": duration,
            "handoff_frames_are_output": False,
            "on_boundary_failure": "retain the approved master timeline and rerender only the failed section or boundary",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(make_plan(args.duration), indent=2))
    except ValueError as error:
        print(json.dumps({"ready": False, "error": str(error)}))
        return 64
    return 0


if __name__ == "__main__":
    sys.exit(main())
