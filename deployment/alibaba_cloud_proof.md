# Alibaba Cloud Deployment Proof

Devpost (Track 2) requires **proof the backend uses Alibaba Cloud**, via a code file
that demonstrates Alibaba Cloud service/API usage.

## Proof code (already present)

- **`backend/app/oss_storage.py`** — canonical, unit-tested OSS integration using the
  official `oss2` SDK (`oss2.Auth`, `oss2.Bucket`, `put_object`, `put_object_from_file`).
- **`deployment/alibaba_cloud_services.py`** — standalone proof entrypoint (same OSS API).
- Models run on **Qwen Cloud / Alibaba Cloud Model Studio** (`backend/app/qwen_client.py`,
  `backend/app/video_tasks.py`) — Qwen3.7 + Wan 2.7 via `dashscope-intl.aliyuncs.com`.

This satisfies the requirement even before the public URL is live: the code demonstrably
calls Alibaba Cloud APIs.

## Fill after provisioning (one line each)

| Field | Value |
|---|---|
| Deployment service | `[FILL: ECS + Docker Compose | Function Compute | Container Service ACK]` |
| Region | `[FILL: e.g. ap-southeast-1]` |
| Backend URL (live) | `[FILL: https://...]` |
| OSS bucket | `[FILL]` |
| Devpost proof link | `[FILL: https://github.com/<you>/circle-take/blob/main/backend/app/oss_storage.py]` |

See `deployment/ecs_or_fc_deploy.md` for the step-by-step deploy runbook.

## Quick verification (after deploy)

```bash
curl -sI https://<backend-url>/health        # expect 200
python -c "from deployment.alibaba_cloud_services import deployment_proof_summary; print(deployment_proof_summary())"
```
