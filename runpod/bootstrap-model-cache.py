#!/usr/bin/env python3
"""Idempotently prepare Asteriq's shared open-weight model cache.

This program downloads no model during Docker image build.  At worker boot it
uses one network-volume lock so concurrent Serverless workers share one cache.
It writes a readiness report and fails closed if a required artifact is absent.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen


MANIFEST = Path("/opt/asteriq/model-cache-manifest.json")


def sha256_file(path: Path) -> str:
    """Hash an artifact without loading a multi-gigabyte weight into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    lock_path = root / "asteriq" / "model-cache-integrity-lock.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap = os.environ.get("ASTERIQ_MODEL_CACHE_BOOTSTRAP", "0") == "1"
    statuses = []

    with (root / "asteriq" / "model-cache.lock").open("w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        integrity_lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {"artifacts": {}}
        locked_artifacts = integrity_lock.setdefault("artifacts", {})
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
            digest = sha256_file(target)
            expected_digest = artifact.get("sha256") or locked_artifacts.get(artifact["id"], {}).get("sha256")
            if expected_digest and digest.lower() != str(expected_digest).lower():
                raise RuntimeError(f"cache integrity check failed for {artifact['id']}")
            # The first cache warm records a content-addressed lock under the
            # shared-volume lock. Later workers must match it exactly; this
            # catches partial writes and later volume corruption.
            locked_artifacts[artifact["id"]] = {"sha256": digest, "bytes": target.stat().st_size}
            statuses.append({
                "id": artifact["id"], "status": "ready", "bytes": target.stat().st_size,
                "sha256": digest, "integrity": "manifest" if artifact.get("sha256") else "shared_cache_lock",
            })
        lock_path.write_text(json.dumps(integrity_lock, indent=2), encoding="utf-8")

    ready = all(item["status"] == "ready" for item in statuses)
    report_path.write_text(json.dumps({"ready": ready, "artifacts": statuses}, indent=2), encoding="utf-8")
    print(f"Asteriq cache readiness: {json.dumps({'ready': ready, 'artifacts': statuses})}", flush=True)
    return 0 if ready else 78


if __name__ == "__main__":
    sys.exit(main())
