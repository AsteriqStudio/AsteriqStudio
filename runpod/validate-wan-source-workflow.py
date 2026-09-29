#!/usr/bin/env python3
"""Static, no-render validation for Asteriq's Wan VACE source-video graph."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys


WORKFLOW = Path("/opt/asteriq/workflows/wan_vace_source_video_api.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, default=WORKFLOW)
    args = parser.parse_args()
    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    nodes = {node_id: node["class_type"] for node_id, node in workflow.items()}
    needed = {"UNETLoader", "CLIPLoader", "VAELoader", "LoadVideo", "LoadImage", "GetVideoComponents", "WanVaceToVideo", "LoraLoader", "KSampler", "TrimVideoLatent", "CreateVideo", "SaveVideo"}
    errors = []
    missing = sorted(needed - set(nodes.values()))
    if missing:
        errors.append(f"missing node types: {', '.join(missing)}")
    serialized = json.dumps(workflow).lower()
    if "ltx" in serialized:
        errors.append("LTX reference found in Wan-only source-video workflow")
    if "wan2.1_vace_1.3b_fp16.safetensors" not in serialized:
        errors.append("expected Wan VACE 1.3B model is not selected")
    if "wan21_causvid_bidirect2_t2v_1_3b_lora_rank32.safetensors" not in serialized:
        errors.append("the required 1.3B CausVid LoRA is missing from the four-step workflow")
    if "umt5_xxl_fp8_e4m3fn_scaled.safetensors" not in serialized or "wan_2.1_vae.safetensors" not in serialized:
        errors.append("Wan text encoder or VAE is not selected")
    sampler = workflow.get("12", {}).get("inputs", {})
    if sampler.get("steps") != 4 or sampler.get("control_after_generate") != "fixed":
        errors.append("checkpoint sampler is not deterministic economy configuration")
    if sampler.get("model") != ["11", 0] or workflow.get("11", {}).get("inputs", {}).get("model") != ["16", 0]:
        errors.append("four-step sampler must use the CausVid-adapted model")
    if workflow.get("13", {}).get("inputs", {}).get("samples") != ["17", 0] or workflow.get("17", {}).get("inputs", {}).get("trim_amount") != ["10", 3]:
        errors.append("reference-image latent must be trimmed before VAE decode")
    vace = workflow.get("10", {}).get("inputs", {})
    if any(node.get("class_type") == "Canny" for node in workflow.values()):
        errors.append("control video must be the prepared source frames; an active Canny edge stream is not the official VACE path")
    if vace.get("control_video") != ["6", 0] or workflow.get("6", {}).get("class_type") != "GetVideoComponents":
        errors.append("WanVaceToVideo control_video must come from the prepared source frames")
    if vace.get("length") != 264:
        errors.append("checkpoint must contain 264 frames: 240 output frames plus a 24-frame temporal handoff at 24 fps")
    report = {"ready": not errors, "errors": errors, "node_types": sorted(set(nodes.values())), "policy": "static validation only; no inference performed"}
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 78


if __name__ == "__main__":
    sys.exit(main())
