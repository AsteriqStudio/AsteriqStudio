#!/usr/bin/env python3
"""Queue-based Runpod handlers for Asteriq's non-video production stages.

These handlers intentionally separate cheap validation from media generation.
``preflight`` never downloads a model, generates a frame, changes a voice, or
renders a Blender scene.  The controller can use that operation to prove a
stage is bootable before an operator approves a production job.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import runpod


STAGE = os.environ.get("ASTERIQ_STAGE", "capture")
# Runpod may mount a Serverless Network Volume at /workspace even when a
# template requested /runpod-volume.  Accept both canonical paths rather than
# reporting a false cache failure after a successful worker start.
_requested_root = Path(os.environ.get("ASTERIQ_VOLUME_ROOT", "/runpod-volume"))
VOLUME_ROOT = _requested_root if _requested_root.is_dir() else Path("/workspace")
MODEL_ROOT = VOLUME_ROOT / "models"


def _binary(name: str) -> str | None:
    return shutil.which(name)


def _cache_items() -> dict[str, bool]:
    # Model weights are deliberately kept off the container layer.  A missing
    # model is a fail-closed result, never a silent remote download or a paid
    # API fallback.
    expected = {
        "capture": [MODEL_ROOT / "pose", MODEL_ROOT / "sam2"],
        "audio": [MODEL_ROOT / "voice" / "openvoice_v2", MODEL_ROOT / "speech" / "faster_whisper_small", MODEL_ROOT / "translation"],
        "direct_3d": [MODEL_ROOT / "trellis"],
    }.get(STAGE, [])
    return {str(path.relative_to(MODEL_ROOT)): path.exists() for path in expected}


def readiness() -> dict[str, Any]:
    cache = _cache_items()
    details: dict[str, Any] = {
        "stage": STAGE,
        "serverless_only": True,
        "volume_root": str(VOLUME_ROOT),
        "volume_mounted": VOLUME_ROOT.is_dir(),
        "ffmpeg": bool(_binary("ffmpeg")),
        "cache": cache,
        "models_ready": bool(cache) and all(cache.values()),
        "generation_enabled": bool(cache) and all(cache.values()),
        "paid_model_apis": False,
    }
    if STAGE == "capture":
        try:
            import mediapipe  # noqa: F401
            import cv2  # noqa: F401
            details["runtime"] = {"mediapipe": True, "opencv": True}
        except ImportError:
            details["runtime"] = {"mediapipe": False, "opencv": False}
    elif STAGE == "audio":
        try:
            import faster_whisper  # noqa: F401
            details["runtime"] = {"faster_whisper": True, "openvoice_source": Path("/opt/openvoice").is_dir()}
        except ImportError:
            details["runtime"] = {"faster_whisper": False, "openvoice_source": Path("/opt/openvoice").is_dir()}
    elif STAGE == "direct_3d":
        blender = _binary("blender")
        version = None
        if blender:
            completed = subprocess.run([blender, "--version"], check=False, capture_output=True, text=True, timeout=20)
            version = completed.stdout.splitlines()[0] if completed.returncode == 0 and completed.stdout else None
        details["runtime"] = {"blender": version, "trellis_source": Path("/opt/TRELLIS").is_dir()}
    return details


def _audio_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    profiles = payload.get("profiles") or []
    seen: set[str] = set()
    errors: list[str] = []
    for profile in profiles:
        character = str(profile.get("character_version_id", ""))
        if not character or not profile.get("consent") or not profile.get("locked_profile_id"):
            errors.append("each voice requires a consent-backed locked character profile")
            continue
        print_id = hashlib.sha256(json.dumps({k: profile.get(k) for k in ("presentation", "treatment", "pitch_shift", "tempo", "tone_color_seed")}, sort_keys=True).encode()).hexdigest()[:16]
        if print_id in seen:
            errors.append("different characters cannot share identical voice settings")
        seen.add(print_id)
    subtitles = payload.get("subtitles") or {}
    if subtitles.get("languages") != ["en", "de"]:
        errors.append("English and German subtitle tracks are required")
    if subtitles.get("style") not in {"yellow_no_box", "black_outline_no_box"}:
        errors.append("subtitle style must be yellow-no-box or black-outline-no-box")
    return {"contract_ready": not errors, "errors": errors, "profile_fingerprints": sorted(seen)}


def _direct_3d_preflight(payload: dict[str, Any]) -> dict[str, Any]:
    character = payload.get("character") or {}
    scene = payload.get("scene") or {}
    errors = [f"character.{key} is required" for key in ("id", "asset_version_id", "height_cm", "design_brief") if not character.get(key)]
    errors += [f"character.{key} must be approved" for key in ("turntable_approved", "rig_approved", "clothing_approved") if character.get(key) is not True]
    errors += [f"scene.{key} is required" for key in ("virtual_set_version_id", "camera_plan_id", "lighting_plan_id", "shot_list_id") if not scene.get(key)]
    output = payload.get("output") or {}
    if output.get("resolution") == "4k" and not output.get("approved_hd_edit_id"):
        errors.append("4K requires an approved HD master")
    return {"contract_ready": not errors, "errors": errors, "direct_3d": True}


def handler(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("input") or {}
    operation = payload.get("operation", "preflight")
    report = readiness()
    if operation == "preflight":
        if STAGE == "audio":
            report["contract"] = _audio_preflight(payload)
        elif STAGE == "direct_3d":
            report["contract"] = _direct_3d_preflight(payload)
        report["no_render"] = True
        return report
    if operation != "approved_execute":
        return {"error": "operation must be preflight or approved_execute"}
    if payload.get("operator_render_approval") != "approved":
        return {"error": "operator approval is required before compute"}
    if not report["generation_enabled"]:
        return {"error": "stage cache is not ready", "readiness": report}
    # The long-running media functions are enabled only after their model
    # caches have been verified.  This guard prevents a malformed client from
    # consuming GPU time merely by calling a stage endpoint.
    return {"error": "execution adapter is locked until this job has an approved controller ticket", "readiness": report}


runpod.serverless.start({"handler": handler})
