#!/usr/bin/env python3
"""Validate the HD-master-only 4K finishing graph without GPU work."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, default=Path("/opt/asteriq/workflows/realesrgan_approved_hd_to_4k_api.json"))
    args = parser.parse_args()
    graph = json.loads(args.workflow.read_text(encoding="utf-8"))
    nodes = {node["class_type"] for node in graph.values()}
    required = {"LoadVideo", "GetVideoComponents", "UpscaleModelLoader", "ImageUpscaleWithModel", "ImageScale", "CreateVideo", "SaveVideo"}
    errors = []
    if required - nodes:
        errors.append(f"missing node types: {', '.join(sorted(required - nodes))}")
    serialized = json.dumps(graph)
    if "APPROVED_HD_MASTER" not in serialized or "APPROVED_HD_EDIT_ID" not in serialized:
        errors.append("4K workflow must require an approved HD master and edit id")
    if '"fps": 24' not in serialized or "FINAL_WIDTH" not in serialized or "FINAL_HEIGHT" not in serialized:
        errors.append("4K workflow must preserve the HD master's 24 fps cadence")
    print(json.dumps({"ready": not errors, "no_render": True, "errors": errors, "policy": "never regenerate animation during 4K finish"}, indent=2))
    return 0 if not errors else 78


if __name__ == "__main__":
    raise SystemExit(main())
