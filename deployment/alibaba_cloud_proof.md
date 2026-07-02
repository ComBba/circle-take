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

## Deployment (provisioned & verified 2026-07-02)

| Field | Value |
|---|---|
| Deployment service | **Alibaba Cloud ECS + Docker Compose** |
| Instance | `i-t4n9vck3xkdijyhfxeb3` ("circletake-proof") · `ecs.e-c1m2.large` (2 vCPU / 4 GB) · Ubuntu 24.04 |
| Region / Zone | `ap-southeast-1` (Singapore) / `ap-southeast-1a` |
| Backend URL | `http://43.98.203.221:8000` — `/health` → 200, `/ui/` demo → 200 |
| OSS bucket | `circle-take-media` (`oss-ap-southeast-1.aliyuncs.com`) |
| Devpost proof link | `https://github.com/ComBba/circle-take/blob/main/backend/app/alibaba_cloud_integration.py` |
| Console screenshot | `docs/screenshots/alibaba-deployment.png` (ECS console → instance `circletake-proof` Running) |

Verified: `curl http://43.98.203.221:8000/health` → `{"status":"ok","service":"circle-take","mode":"fixture"}`
(HTTP 200); container `circle-take-api-1` **Up (healthy)**. The backend runs on Alibaba Cloud ECS; Qwen
(DashScope, `dashscope-intl.aliyuncs.com`) + OSS are exercised by the code (see the proof-link file).

See `deployment/ecs_or_fc_deploy.md` for the step-by-step deploy runbook.

## Quick verification (after deploy)

```bash
curl -sI https://<backend-url>/health        # expect 200
python -c "from deployment.alibaba_cloud_services import deployment_proof_summary; print(deployment_proof_summary())"
```
