# Media hand-off: RunPod Serverless

The `asteriq-media-production` Network Volume is the private S3-compatible
store for production media. It is deliberately separate from the model cache.

## What belongs where

- `/runpod-volume/models` on `asteriq-ltx-models`: model weights, node assets,
  and worker-local model cache only.
- `s3://<media-volume>/media/source/...`: original uploaded video or image.
- `s3://<media-volume>/media/cfr/...`: a single constant-24fps source conform.
- `s3://<media-volume>/media/tracks/...`: masks, poses, camera solve, and a
  continuity manifest keyed by the source hash.
- `s3://<media-volume>/media/sections/...`: chronological 10-second working
  sections and their 24-frame handoff data. Handoff data conditions the next
  section; it is never duplicated in the final edit.
- `s3://<media-volume>/deliveries/hd/...` and `/deliveries/4k/...`: approved
  masters and subtitle sidecars.

No model weight, container layer, or anonymous upload is stored in the media
volume. No source-video object is uploaded until an operator selects it in the
studio and the no-render preflight accepts its cast assignments.

## Required Serverless environment

Every worker that reads or writes production media needs these settings:

```text
ASTERIQ_MEDIA_PROVIDER=runpod_s3
ASTERIQ_S3_BUCKET=<media Network Volume ID>
ASTERIQ_S3_REGION=eu-ro-1
ASTERIQ_S3_ENDPOINT=https://s3api-eu-ro-1.runpod.io
AWS_ACCESS_KEY_ID=<RunPod S3 access key>
AWS_SECRET_ACCESS_KEY={{ RUNPOD_SECRET_<dedicated-s3-secret> }}
```

The access key identifies the account. The secret must be selected with
RunPod's Secret picker and must never be committed, printed in a readiness
report, or placed in a client bundle. The stage worker's `storage_preflight`
operation reports only whether all settings are present.

## Retention policy

Keep the source, the approved continuity manifest, the current HD master, and
the final subtitle tracks. Delete transient masks, rejected previews, and
superseded section attempts only after their replacement passes the boundary
gate. Create 4K from an approved HD master, then download or archive that
locked deliverable before removing its remote copy.
