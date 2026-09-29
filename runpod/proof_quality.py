#!/usr/bin/env python3
"""Reject unusable Wan VACE proofs before audio or later sections start.

The checker is pixel-only. It does not start ComfyUI, download weights, or
submit a GPU job. A file that merely exists as an MP4 is not a passed proof.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageFilter, ImageStat


APPROVED_ANCHOR_ORIGINS = {"approved_anime_sheet", "source_frame"}
REJECTED_ANCHOR_ORIGINS = {
    "starter_glb_preview",
    "procedural_placeholder",
    "glb_viewport",
    "blocky_starter",
}
MINIMUM_ANCHOR_SHORT_SIDE = 480
# A 24-pixel nearest-neighbor starter reconstructs below this error.
# The wardrobe source frame measures about 10.
LOW_DETAIL_RECONSTRUCTION_ERROR = 4.0


def _load(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def _channel_means(image: Image.Image) -> tuple[float, float, float]:
    red, green, blue = ImageStat.Stat(image).mean
    return float(red), float(green), float(blue)


def _edge_mean(image: Image.Image) -> float:
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).mean[0])


def _laplacian_stddev(image: Image.Image) -> float:
    lap = image.convert("L").filter(
        ImageFilter.Kernel((3, 3), [-1, -1, -1, -1, 8, -1, -1, -1, -1], scale=1, offset=128)
    )
    return float(ImageStat.Stat(lap).stddev[0])


def _reconstruction_error(image: Image.Image, short_side: int = 48) -> float:
    width, height = image.size
    if width <= height:
        small_size = (short_side, max(1, round(height * short_side / width)))
    else:
        small_size = (max(1, round(width * short_side / height)), short_side)
    reduced = image.resize(small_size, Image.Resampling.BOX)
    reconstructed = reduced.resize(image.size, Image.Resampling.NEAREST)
    difference = ImageChops.difference(image, reconstructed)
    return sum(ImageStat.Stat(difference).mean) / 3.0


def _subject_axis_degrees(image: Image.Image) -> float:
    """0 means the subject lies across the frame. 90 means upright."""
    width = 96
    height = max(1, round(image.height * width / image.width))
    small = image.resize((width, height))
    pixels = list(small.getdata())
    corners = (pixels[0], pixels[width - 1], pixels[(height - 1) * width], pixels[-1])
    background = tuple(sum(pixel[channel] for pixel in corners) / 4 for channel in range(3))
    xs: list[float] = []
    ys: list[float] = []
    for index, pixel in enumerate(pixels):
        distance = sum((pixel[channel] - background[channel]) ** 2 for channel in range(3)) ** 0.5
        if distance > 28:
            xs.append(index % width)
            ys.append(index // width)
    if len(xs) < 30:
        return 90.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    angle = abs(math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy)))
    return min(angle, 180 - angle)


def inspect_frame(path: Path) -> dict:
    image = _load(path)
    red, green, blue = _channel_means(image)
    edge_mean = _edge_mean(image)
    lap_std = _laplacian_stddev(image)
    blue_channel_collapse = blue >= 170 and blue >= max(red, green) + 80
    severe_ghosting = lap_std < 8.0 and edge_mean < 2.5
    short_side = min(image.size)
    detail_error = _reconstruction_error(image)
    low_detail_preview = short_side < MINIMUM_ANCHOR_SHORT_SIDE or detail_error < LOW_DETAIL_RECONSTRUCTION_ERROR
    subject_axis = _subject_axis_degrees(image)
    sideways_subject = subject_axis < 25
    reasons = []
    if blue_channel_collapse:
        reasons.append("blue-channel collapse")
    if severe_ghosting:
        reasons.append("severe ghosting")
    if sideways_subject:
        reasons.append("subject is sideways")
    return {
        "path": str(path),
        "width": image.size[0],
        "height": image.size[1],
        "channel_means": {"red": round(red, 2), "green": round(green, 2), "blue": round(blue, 2)},
        "edge_mean": round(edge_mean, 2),
        "laplacian_stddev": round(lap_std, 2),
        "reconstruction_error": round(detail_error, 2),
        "blue_channel_collapse": blue_channel_collapse,
        "severe_ghosting": severe_ghosting,
        "low_detail_preview": low_detail_preview,
        "subject_axis_degrees": round(subject_axis, 1),
        "sideways_subject": sideways_subject,
        "passed": not reasons,
        "reasons": reasons,
    }


def inspect_anchor(path: Path | None, metadata: dict | None = None) -> dict:
    metadata = metadata or {}
    origin = metadata.get("origin")
    approval = metadata.get("approval")
    reasons = []
    if approval != "production":
        reasons.append("paid animation requires a production character anchor")
    if origin in REJECTED_ANCHOR_ORIGINS:
        reasons.append("starter GLB preview cannot be used as a paid-animation reference")
    elif origin not in APPROVED_ANCHOR_ORIGINS:
        reasons.append("character anchor must be an approved anime sheet or the source frame")
    frame_report = None
    if path is not None:
        frame_report = inspect_frame(path)
        if frame_report["low_detail_preview"]:
            reasons.append("character anchor is a low-detail starter preview")
        if frame_report["blue_channel_collapse"] or frame_report["severe_ghosting"] or frame_report["sideways_subject"]:
            reasons.append("character anchor failed the same frame-quality gate as a proof")
    return {
        "anchor_ready": not reasons,
        "origin": origin,
        "approval": approval,
        "reasons": reasons,
        "frame_report": frame_report,
    }


def evaluate_proof(proof: dict) -> list[str]:
    """Return reasons a delivered render must not continue into audio."""
    if not isinstance(proof, dict):
        return ["rendered proof must be an object"]
    frame_path = proof.get("frame_path")
    report = proof.get("quality_report")
    if proof.get("mp4_present") and not frame_path and not isinstance(report, dict):
        return ["an MP4 alone does not complete a proof"]
    if frame_path:
        report = inspect_frame(Path(frame_path))
    elif not isinstance(report, dict):
        return ["proof quality report is required before audio or later sections"]
    errors = []
    if report.get("blue_channel_collapse"):
        errors.append("proof failed: blue-channel collapse")
    if report.get("severe_ghosting"):
        errors.append("proof failed: severe ghosting")
    if report.get("sideways_subject"):
        errors.append("proof failed: subject is sideways")
    if report.get("passed") is not True and not errors:
        errors.append("proof quality report did not pass")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("frame", type=Path)
    parser.add_argument("--anchor-origin")
    parser.add_argument("--anchor-approval")
    args = parser.parse_args()
    if args.anchor_origin or args.anchor_approval:
        report = inspect_anchor(args.frame, {"origin": args.anchor_origin, "approval": args.anchor_approval})
    else:
        report = inspect_frame(args.frame)
    print(json.dumps(report, indent=2))
    ready = report.get("passed", report.get("anchor_ready"))
    return 0 if ready else 78


if __name__ == "__main__":
    sys.exit(main())
