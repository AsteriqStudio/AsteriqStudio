#!/usr/bin/env python3
"""Install stage weights on the attached model cache only when requested."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil

def has_payload(path: Path) -> bool:
    return path.is_dir() and sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) >= 1_048_576


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("capture", "audio", "direct_3d"), required=True)
    args = parser.parse_args()
    root = Path(os.environ.get("ASTERIQ_MODEL_ROOT", "/runpod-volume/models"))
    manifest = json.loads(Path("/opt/asteriq/stage-cache-manifest.json").read_text(encoding="utf-8"))
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < 4 * 1024**3:
        raise RuntimeError("model cache has less than 4 GiB free; do not mix media with model weights")
    lock_path = root / "asteriq" / "stage-cache.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        for artifact in manifest["stages"][args.stage]:
            target = root / artifact["destination"]
            if has_payload(target):
                print(f"Asteriq stage cache: using {artifact['id']}", flush=True)
                continue
            print(f"Asteriq stage cache: downloading {artifact['id']}", flush=True)
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=artifact["repository"], revision=artifact["revision"], local_dir=str(target))
            if not has_payload(target):
                raise RuntimeError(f"stage cache artifact was unexpectedly small: {artifact['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
