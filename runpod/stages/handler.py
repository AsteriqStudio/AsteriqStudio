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
# Runpod's Serverless mount is /runpod-volume.  Prefer that canonical mount
# even if an old endpoint setting still provides /workspace: /workspace is
# always present in many images and would otherwise hide the real cache.
_canonical_root = Path("/runpod-volume")
_requested_root = Path(os.environ.get("ASTERIQ_VOLUME_ROOT", "/runpod-volume"))
if _canonical_root.is_dir():
    VOLUME_ROOT = _canonical_root
elif _requested_root.is_dir():
    VOLUME_ROOT = _requested_root
else:
    VOLUME_ROOT = Path("/workspace")
MODEL_ROOT = VOLUME_ROOT / "models"


def _binary(name: str) -> str | None:
    return shutil.which(name)


def _cache_items() -> dict[str, bool]:
    # Model weights are deliberately kept off the container layer.  A missing
    # model is a fail-closed result, never a silent remote download or a paid
    # API fallback.
    expected = {
        "capture": [MODEL_ROOT / "pose", MODEL_ROOT / "sam2"],
        # Keep these paths aligned with the shared stage-cache manifest.
        # Previous drafts used incompatible layouts and could report an
        # installed cache as missing.
        "audio": [MODEL_ROOT / "audio" / "openvoice-v2", MODEL_ROOT / "audio" / "faster-whisper-small", MODEL_ROOT / "audio" / "marian-en-de", MODEL_ROOT / "audio" / "marian-de-en", MODEL_ROOT / "audio" / "latentsync-1.6"],
        "direct_3d": [MODEL_ROOT / "trellis"],
    }.get(STAGE, [])
    return {str(path.relative_to(MODEL_ROOT)): path.exists() for path in expected}


def _core_cache_report() -> dict[str, Any]:
    """Expose only cache readiness state, never paths or credential data."""
    report_path = MODEL_ROOT / "asteriq" / "model-cache-readiness.json"
    if not report_path.is_file():
        return {"report_present": False, "ready": False, "artifacts": []}
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"report_present": True, "ready": False, "artifacts": []}
    artifacts = report.get("artifacts") or []
    return {
        "report_present": True,
        "ready": report.get("ready") is True and all(item.get("status") == "ready" for item in artifacts),
        "artifacts": [{"id": item.get("id"), "status": item.get("status")} for item in artifacts],
    }


def _media_storage() -> dict[str, Any]:
    """Describe the S3 hand-off without exposing credentials in any report."""
    fields = {
        "bucket": os.environ.get("ASTERIQ_S3_BUCKET"),
        "region": os.environ.get("ASTERIQ_S3_REGION"),
        "endpoint": os.environ.get("ASTERIQ_S3_ENDPOINT"),
        "access_key": os.environ.get("AWS_ACCESS_KEY_ID"),
        "secret": os.environ.get("AWS_SECRET_ACCESS_KEY"),
    }
    missing = [name for name, value in fields.items() if not value]
    return {
        "provider": os.environ.get("ASTERIQ_MEDIA_PROVIDER", "unconfigured"),
        "configured": not missing,
        "missing": missing,
        "bucket": fields["bucket"],
        "region": fields["region"],
        "endpoint": fields["endpoint"],
    }


def readiness() -> dict[str, Any]:
    cache = _cache_items()
    media_storage = _media_storage()
    details: dict[str, Any] = {
        "stage": STAGE,
        "serverless_only": True,
        "volume_root": str(VOLUME_ROOT),
        "volume_mounted": VOLUME_ROOT.is_dir(),
        "ffmpeg": bool(_binary("ffmpeg")),
        "cache": cache,
        "core_model_cache": _core_cache_report(),
        "models_ready": bool(cache) and all(cache.values()),
        "generation_enabled": bool(cache) and all(cache.values()),
        "paid_model_apis": False,
        "media_storage": media_storage,
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
    """Validate a locked synthetic/consented voice and final-waveform lip-sync plan."""
    profiles = payload.get("profiles") or []
    seen: set[str] = set()
    errors: list[str] = []
    if not profiles:
        errors.append("at least one saved character voice profile is required")
    for profile in profiles:
        character = str(profile.get("character_version_id") or profile.get("character_id") or "")
        locked_id = str(profile.get("locked_profile_id") or "")
        if not character or not locked_id or profile.get("tone_color_seed") is None:
            errors.append("each voice requires a saved locked character profile")
            continue
        # A fictional synthetic profile can be directed without copying a human.
        # Consent is mandatory only when a real reference clip is supplied.
        if profile.get("reference_voice_uri") and profile.get("reference_voice_consent") is not True:
            errors.append(f"{character}: a real reference voice needs saved consent")
        print_id = hashlib.sha256(json.dumps({
            "character": character,
            "profile": locked_id,
            "presentation": profile.get("presentation"),
            "style": profile.get("style", profile.get("treatment")),
            "pitch": profile.get("pitch_shift"),
            "formant": profile.get("formant_shift"),
            "tone": profile.get("tone_color_seed"),
            "direction": profile.get("voice_direction", ""),
        }, sort_keys=True).encode()).hexdigest()[:16]
        if print_id in seen:
            errors.append("different characters cannot share identical voice settings")
        seen.add(print_id)
    subtitles = payload.get("subtitles") or {}
    if subtitles.get("languages") != ["en", "de"]:
        errors.append("English and German subtitle tracks are required")
    if subtitles.get("style") not in {"yellow_no_box", "black_outline_no_box"}:
        errors.append("subtitle style must be yellow-no-box or black-outline-no-box")
    dialogue = str(payload.get("dialogue") or "").strip()
    lip_sync = payload.get("lip_sync") or {}
    if dialogue:
        if lip_sync.get("required") is not True:
            errors.append("dialogue requires lip-sync")
        if lip_sync.get("quality_gate") != "phoneme_timing_matches_final_waveform":
            errors.append("lip-sync must be checked against the final waveform")
    overlays = payload.get("on_screen_text") or ""
    return {
        "contract_ready": not errors,
        "errors": errors,
        "profile_fingerprints": sorted(seen),
        "dialogue_present": bool(dialogue),
        "visible_text_present": bool(overlays),
        "ordered_pipeline": ["synthesize_or_convert", "freeze_final_waveform", "LatentSync_1_6", "timed_transcription", "en_de_translation", "subtitle_export", "overlay_and_mux"],
        "outputs": ["character_dialogue.wav", "lip_synced_video.mp4", "en.vtt", "de.vtt", "en.ass", "de.ass", "captioned_master.mp4"],
    }

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
    if operation in {"preflight", "storage_preflight"}:
        if STAGE == "audio":
            report["contract"] = _audio_preflight(payload)
        elif STAGE == "direct_3d":
            report["contract"] = _direct_3d_preflight(payload)
        report["no_render"] = True
        report["media_handoff_ready"] = report["media_storage"]["configured"]
        return report
    if operation == "cache_install":
        # Cache installation is never implicit at boot or preflight. It can
        # download open weights, so an explicit operator approval is required.
        if payload.get("operator_cache_install_approval") != "approved":
            return {"error": "operator cache-install approval is required", "readiness": report}
        installer = Path("/opt/asteriq/bootstrap-stage-cache.py")
        if not installer.is_file():
            return {"error": "stage cache installer is not present", "readiness": report}
        completed = subprocess.run(["python", str(installer), "--stage", STAGE], check=False, capture_output=True, text=True, timeout=60 * 60)
        refreshed = readiness()
        return {"stage": STAGE, "cache_install_exit_code": completed.returncode, "models_ready": refreshed["models_ready"], "readiness": refreshed, "log_tail": (completed.stdout + completed.stderr)[-4000:]}
    if operation != "approved_execute":
        return {"error": "operation must be preflight, storage_preflight, cache_install, or approved_execute"}
    if payload.get("operator_render_approval") != "approved":
        return {"error": "operator approval is required before compute"}
    if not report["generation_enabled"]:
        return {"error": "stage cache is not ready", "readiness": report}
    if not report["media_storage"]["configured"]:
        return {"error": "stage media storage is not configured", "readiness": report}
    # The long-running media functions are enabled only after their model
    # caches have been verified.  This guard prevents a malformed client from
    # consuming GPU time merely by calling a stage endpoint.
    return {"error": "execution adapter is locked until this job has an approved controller ticket", "readiness": report}


runpod.serverless.start({"handler": handler})
