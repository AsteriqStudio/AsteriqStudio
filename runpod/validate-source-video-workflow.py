#!/usr/bin/env python3
"""Write an honest source-video workflow capability report at worker boot.

The Comfy worker supplies ingest/tracking foundations.  Blender, audio and
subtitle processing are deliberately separate services and remain unavailable
until their own pinned workers have reported ready.  This validator never
launches ComfyUI, Blender, audio conversion, or inference.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys


MANIFEST = Path("/opt/asteriq/source-video-workflow-manifest.json")
MODEL_ROOT = Path("/runpod-volume/models")
COMFY_ROOT = Path("/comfyui")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    requirements = manifest["core_comfy_requirements"]
    available_nodes = {
        node: (COMFY_ROOT / "custom_nodes" / node).is_dir()
        for node in requirements["nodes"]
    }
    available_models = {
        model: (MODEL_ROOT / model).is_file() and (MODEL_ROOT / model).stat().st_size >= 1_048_576
        for model in requirements["models"]
    }
    available_executables = {command: shutil.which(command) is not None for command in requirements["executables"]}
    blender_ready = shutil.which("blender") is not None
    audio_runtime_ready = Path("/opt/asteriq/audio-venv/bin/python").is_file() and Path("/opt/asteriq/openvoice").is_dir()
    audio_models = {
        "openvoice": (MODEL_ROOT / "audio/openvoice-v2").is_dir(),
        "asr": (MODEL_ROOT / "audio/faster-whisper-small").is_dir(),
        "en_de": (MODEL_ROOT / "audio/marian-en-de").is_dir(),
        "de_en": (MODEL_ROOT / "audio/marian-de-en").is_dir(),
    }
    base_ready = all(available_nodes.values()) and all(available_models.values()) and all(available_executables.values())
    capabilities = {
        "source_ingest": available_executables.get("ffmpeg", False) and available_nodes.get("ComfyUI-VideoHelperSuite", False),
        "performer_tracking": available_nodes.get("ComfyUI-segment-anything-2", False) and available_models.get("sam2/sam2.1_hiera_tiny-fp16.safetensors", False),
        "motion_capture": available_nodes.get("ComfyUI-segment-anything-2", False) and audio_runtime_ready,
        "rig_retarget": blender_ready,
        "virtual_set_render": blender_ready,
        "voice_conversion": audio_runtime_ready and audio_models["openvoice"],
        "local_subtitles": audio_runtime_ready and all(audio_models[key] for key in ("asr", "en_de", "de_en")),
        "frame_assembly": available_executables.get("ffmpeg", False),
    }
    blockers = [name for name, ready in capabilities.items() if not ready]
    report = {
        "workflow_version": manifest["workflow_version"],
        "base_comfy_ready": base_ready,
        "node_checks": available_nodes,
        "model_checks": available_models,
        "executable_checks": available_executables,
        "blender_ready": blender_ready,
        "audio_runtime_ready": audio_runtime_ready,
        "audio_model_checks": audio_models,
        "capabilities": capabilities,
        "full_production_ready": not blockers,
        "blocking_capabilities": blockers,
        "policy": "do_not_submit_source_video_job_until_full_production_ready_is_true",
    }
    report_path = MODEL_ROOT / "asteriq" / "source-video-workflow-readiness.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Asteriq source-video workflow readiness: {json.dumps(report)}", flush=True)
    # The Comfy foundations are a separate health boundary from the future
    # Blender/audio workers.  Fail a broken base image, but report the latter
    # as unavailable instead of claiming that it is installed.
    return 0 if base_ready else 78


if __name__ == "__main__":
    sys.exit(main())
