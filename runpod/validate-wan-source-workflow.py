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
    needed = {"UNETLoader", "CLIPLoader", "VAELoader", "LoadVideo", "LoadImage", "GetVideoComponents", "WanVaceToVideo", "KSampler", "CreateVideo", "SaveVideo"}
    errors = []
    missing = sorted(needed - set(nodes.values()))
    if missing:
        errors.append(f"missing node types: {', '.join(missing)}")
    serialized = json.dumps(workflow).lower()
    if "ltx" in serialized:
        errors.append("LTX reference found in Wan-only source-video workflow")
    if "wan2.1_vace_1.3b_fp16.safetensors" not in serialized:
        errors.append("expected Wan VACE 1.3B model is not selected")
    if "umt5_xxl_fp8_e4m3fn_scaled.safetensors" not in serialized or "wan_2.1_vae.safetensors" not in serialized:
        errors.append("Wan text encoder or VAE is not selected")
    sampler = workflow.get("12", {}).get("inputs", {})
    if sampler.get("steps") != 4 or sampler.get("control_after_generate") != "fixed":
        errors.append("checkpoint sampler is not deterministic economy configuration")
    vace = workflow.get("10", {}).get("inputs", {})
    if vace.get("length") != 241:
        errors.append("checkpoint must contain 241 frames: 10 seconds plus one overlap frame at 24 fps")
    report = {"ready": not errors, "errors": errors, "node_types": sorted(set(nodes.values())), "policy": "static validation only; no inference performed"}
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 78


if __name__ == "__main__":
    sys.exit(main())
