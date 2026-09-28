#!/usr/bin/env python3
"""Queue-based Runpod handlers for Asteriq's non-video production stages.

These handlers intentionally separate cheap validation from media generation.
``preflight`` never downloads a model, generates a frame, changes a voice, or
renders a Blender scene.  The controller can use that operation to prove a
stage is bootable before an operator approves a production job.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
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
        # Capture uses MediaPipe from the image for pose and the SAM2 weight
        # already installed by the shared core cache.  There is intentionally
        # no duplicate /models/pose download.
        "capture": [MODEL_ROOT / "sam2" / "sam2.1_hiera_tiny-fp16.safetensors"],
        # Keep these paths aligned with the shared stage-cache manifest.
        # Previous drafts used incompatible layouts and could report an
        # installed cache as missing.
        "audio": [MODEL_ROOT / "audio" / "openvoice-v2", MODEL_ROOT / "audio" / "faster-whisper-small", MODEL_ROOT / "audio" / "marian-en-de", MODEL_ROOT / "audio" / "marian-de-en", MODEL_ROOT / "audio" / "m2m100-418m", MODEL_ROOT / "audio" / "latentsync-1.6"],
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
        if not all(details["runtime"].values()):
            details["models_ready"] = False
            details["generation_enabled"] = False
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


def _decode_data_uri(value: str, target: Path) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing media payload for {target.name}")
    encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    target.write_bytes(base64.b64decode(encoded, validate=True))
    if target.stat().st_size < 1024:
        raise ValueError(f"decoded media is empty for {target.name}")


def _run_media(command: list[str], timeout: int = 600) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "media command failed")[-3000:])


def _duration(path: Path) -> float:
    completed = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)
    ], check=False, capture_output=True, text=True, timeout=30)
    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"could not read duration for {path.name}") from exc


def _stamp(seconds: float, vtt: bool = False) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    separator = "." if vtt else ","
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{milliseconds:03d}"


def _captions(segments: list[dict[str, Any]], field: str, vtt: bool = False) -> str:
    lines = ["WEBVTT", ""] if vtt else []
    for index, segment in enumerate(segments, 1):
        text = str(segment.get(field) or "").strip()
        if not text:
            continue
        if not vtt:
            lines.append(str(index))
        lines.extend([f"{_stamp(float(segment['start']), vtt)} --> {_stamp(float(segment['end']), vtt)}", text, ""])
    return "\n".join(lines).strip() + "\n"


def _translate(texts: list[str], source: str, target: str) -> list[str]:
    if source == target:
        return texts
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    if source in {"en", "de"} and target in {"en", "de"}:
        model_path = MODEL_ROOT / "audio" / f"marian-{source}-{target}"
        tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(str(model_path), local_files_only=True)
        batch = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        generated = model.generate(**batch, max_new_tokens=192)
    else:
        model_path = MODEL_ROOT / "audio" / "m2m100-418m"
        tokenizer = AutoTokenizer.from_pretrained(str(model_path), src_lang=source, local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(str(model_path), local_files_only=True)
        batch = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        generated = model.generate(**batch, forced_bos_token_id=tokenizer.get_lang_id(target), max_new_tokens=192)
    return tokenizer.batch_decode(generated, skip_special_tokens=True)


def _transcribe(audio_path: Path) -> tuple[str, list[dict[str, Any]]]:
    import torch
    from faster_whisper import WhisperModel
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    model = WhisperModel(str(MODEL_ROOT / "audio" / "faster-whisper-small"), device=device, compute_type=compute_type, local_files_only=True)
    iterator, info = model.transcribe(str(audio_path), beam_size=5, vad_filter=True, word_timestamps=True)
    segments = [{"start": float(item.start), "end": float(item.end), "source": item.text.strip()} for item in iterator if item.text.strip()]
    return str(info.language or "en").lower().split("-")[0], segments


def _audio_execute(payload: dict[str, Any]) -> dict[str, Any]:
    quote_id = str(payload.get("controller_quote_id") or "")
    maximum = float(payload.get("maximum_authorized_usd") or 0)
    if not quote_id or maximum <= 0 or maximum > 10:
        return {"error": "a valid controller quote and bounded authorization are required"}
    subtitle_request = payload.get("subtitles") or {}
    if set(subtitle_request.get("languages") or []) != {"source", "en", "de"}:
        return {"error": "source, English and German subtitle tracks are required"}
    lip_sync = payload.get("lip_sync") or {}
    if lip_sync.get("required") is not True or lip_sync.get("timing_policy") != "preserve_source_timing":
        return {"error": "the source-timing lip-sync contract is required"}

    with tempfile.TemporaryDirectory(prefix="asteriq-audio-") as folder_name:
        folder = Path(folder_name)
        source_video = folder / "source.mp4"
        animated_video = folder / "animated.mp4"
        source_audio = folder / "source.wav"
        altered_audio = folder / "altered.wav"
        master = folder / "captioned-master.mp4"
        _decode_data_uri(str(payload.get("source_video") or ""), source_video)
        _decode_data_uri(str(payload.get("animated_video") or ""), animated_video)
        _run_media(["ffmpeg", "-y", "-i", str(source_video), "-vn", "-ar", "48000", "-ac", "1", str(source_audio)])
        duration = _duration(source_audio)

        profile = payload.get("voice_profile") or {}
        pitch = float(profile.get("pitch_shift") or 1.18)
        if pitch < 0.8 or pitch > 1.25:
            pitch = 1.18
        tempo = 1.0 / pitch
        voice_filter = (
            f"highpass=f=85,lowpass=f=10500,asetrate=48000*{pitch:.5f},aresample=48000,"
            f"atempo={tempo:.5f},acompressor=threshold=-18dB:ratio=2.5:attack=15:release=180,"
            f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur={duration:.3f},atrim=0:{duration:.3f}"
        )
        _run_media(["ffmpeg", "-y", "-i", str(source_audio), "-af", voice_filter, "-ar", "48000", "-ac", "1", str(altered_audio)])
        altered_duration = _duration(altered_audio)
        timing_drift_ms = abs(duration - altered_duration) * 1000
        if timing_drift_ms > 80:
            raise RuntimeError(f"altered voice failed the lip-sync duration gate ({timing_drift_ms:.1f} ms drift)")

        source_language, segments = _transcribe(source_audio)
        if not segments:
            end = max(0.5, min(duration, 2.0))
            segments = [{"start": 0.0, "end": end, "source": "[No speech detected]"}]
        source_texts = [item["source"] for item in segments]
        en_texts = _translate(source_texts, source_language, "en")
        de_texts = _translate(source_texts, source_language, "de")
        for item, en_text, de_text in zip(segments, en_texts, de_texts):
            item["en"] = en_text
            item["de"] = de_text

        sidecars: dict[str, str] = {}
        subtitle_files: list[Path] = []
        for field in ("source", "en", "de"):
            for suffix, is_vtt in (("srt", False), ("vtt", True)):
                content = _captions(segments, field, is_vtt)
                sidecars[f"{field}_{suffix}"] = content
                path = folder / f"{field}.{suffix}"
                path.write_text(content, encoding="utf-8")
                if suffix == "srt":
                    subtitle_files.append(path)

        command = ["ffmpeg", "-y", "-i", str(animated_video), "-i", str(altered_audio)]
        for subtitle in subtitle_files:
            command.extend(["-i", str(subtitle)])
        command.extend(["-map", "0:v:0", "-map", "1:a:0", "-map", "2:0", "-map", "3:0", "-map", "4:0"])
        title = str((payload.get("section") or {}).get("text_overlay") or "").strip()
        if title:
            title_file = folder / "title.txt"
            title_file.write_text(title, encoding="utf-8")
            draw = f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile={title_file}:fontcolor=white:fontsize=28:box=1:boxcolor=black@0.55:boxborderw=12:x=(w-text_w)/2:y=h*0.08:enable='between(t,0,3)'"
            command.extend(["-vf", draw, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21"])
        else:
            command.extend(["-c:v", "copy"])
        command.extend([
            "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", f"language={source_language}",
            "-metadata:s:s:0", "title=Source language", "-metadata:s:s:1", "language=eng", "-metadata:s:s:1", "title=English",
            "-metadata:s:s:2", "language=deu", "-metadata:s:s:2", "title=German", "-map_metadata", "-1", "-movflags", "+faststart", "-t", f"{duration:.3f}", str(master),
        ])
        _run_media(command)
        report = {
            "source_language": source_language,
            "subtitle_tracks": ["source", "en", "de"],
            "embedded_subtitles": True,
            "voice_treatment": "timing_locked_privacy_timbre_shift",
            "pitch_factor": pitch,
            "lip_sync_method": "source_performance_motion_with_duration_locked_final_waveform",
            "timing_drift_ms": round(timing_drift_ms, 2),
            "source_duration_seconds": round(duration, 3),
            "master_duration_seconds": round(_duration(master), 3),
        }
        return {"captioned_master_base64": base64.b64encode(master.read_bytes()).decode("ascii"), **sidecars, "report": report}

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
    if STAGE == "audio":
        try:
            return _audio_execute(payload)
        except Exception as exc:
            return {"error": f"audio finishing failed: {type(exc).__name__}: {exc}", "readiness": readiness()}
    # The long-running media functions are enabled only after their model
    # caches have been verified.  This guard prevents a malformed client from
    # consuming GPU time merely by calling a stage endpoint.
    return {"error": "execution adapter is locked until this job has an approved controller ticket", "readiness": report}


runpod.serverless.start({"handler": handler})
