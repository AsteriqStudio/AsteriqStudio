#!/usr/bin/env python3
"""Idempotently prepare Asteriq's shared open-weight model cache.

This program downloads no model during Docker image build.  At worker boot it
uses one network-volume lock so concurrent Serverless workers share one cache.
It writes a readiness report and fails closed if a required artifact is absent.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen


MANIFEST = Path("/opt/asteriq/model-cache-manifest.json")


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            request = Request(url, headers={"User-Agent": "AsteriqStudio/1.0"})
            with urlopen(request, timeout=90) as response:
                shutil.copyfileobj(response, temp)
            if temp_path.stat().st_size < 1_048_576:
                raise RuntimeError(f"download was unexpectedly small: {url}")
            temp_path.replace(destination)
        finally:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    root = Path(manifest["model_root"])
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / "asteriq" / "model-cache-readiness.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap = os.environ.get("ASTERIQ_MODEL_CACHE_BOOTSTRAP", "0") == "1"
    statuses = []

    with (root / "asteriq" / "model-cache.lock").open("w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if bootstrap and shutil.disk_usage(root).free < int(manifest["minimum_free_bytes"]):
            raise RuntimeError("RunPod network volume lacks the 30 GiB free space required for the core model cache")
        for artifact in manifest["artifacts"]:
            target = root / artifact["destination"]
            if not target.is_file() or target.stat().st_size < 1_048_576:
                if not bootstrap:
                    statuses.append({"id": artifact["id"], "status": "missing"})
                    continue
                print(f"Asteriq cache: downloading {artifact['id']}", flush=True)
                download(artifact["source"], target)
            statuses.append({"id": artifact["id"], "status": "ready", "bytes": target.stat().st_size})

    ready = all(item["status"] == "ready" for item in statuses)
    report_path.write_text(json.dumps({"ready": ready, "artifacts": statuses}, indent=2), encoding="utf-8")
    print(f"Asteriq cache readiness: {json.dumps({'ready': ready, 'artifacts': statuses})}", flush=True)
    return 0 if ready else 78


if __name__ == "__main__":
    sys.exit(main())
