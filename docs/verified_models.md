# Verified Models

Status legend: ✅ live-200 confirmed (Task 0.2) · 📄 doc-verified only (pending live) · ❓ candidate

> Fill the ✅ column by running `python scripts/smoke_qwen.py` in Task 0.2 (needs QWEN_API_KEY).
> Only models that return HTTP 200 from the intl endpoint get promoted to "chosen".

## Chosen (live-confirmed 2026-06-21)
| Role | Chosen model | Status | Notes |
|---|---|---|---|
| Text reasoning / contracts | `qwen3.7-plus` | ✅ | HTTP 200 live (chat/completions) |
| Heavy reasoning (optional) | `qwen3.7-max` | ✅ | HTTP 200 live |
| Vision / Continuity Court | `qwen3.7-plus` | ✅ | HTTP 200 live (multimodal) |
| Video T2V (establishing) | `wan2.7-t2v` | ✅ | live task SUCCEEDED -> real mp4 (create→poll) |
| Video I2V (first/last frame) | `wan2.7-i2v` | 📄 | same suite; not yet live-tested |
| Video R2V (character-critical) | `wan2.7-r2v` | 📄 | reference-to-video; not yet live-tested |
| Video edit (reshoot 1순위) | `wan2.7-videoedit` | 📄 | instruction-based editing; not yet live-tested |

## Endpoint / auth (doc-verified)
- Host: `https://dashscope-intl.aliyuncs.com`
- Chat (text/vision): `POST /compatible-mode/v1/chat/completions`
- Video: `POST /api/v1/services/aigc/video-generation/video-synthesis` (`X-DashScope-Async: enable`) → poll `GET /api/v1/tasks/{task_id}` (1–5 min)
- Auth: `Authorization: Bearer $QWEN_API_KEY`

## Smoke test results (2026-06-21, live)
```
TEXT  qwen3.7-plus : 200 OK
TEXT  qwen3.7-max  : 200 OK
VISION qwen3.7-plus: 200 OK
VIDEO wan2.7-t2v   : task 8fa5b9c6-... CREATED -> polled -> SUCCEEDED -> real .mp4 (~3.5MB)
```
Secrets live in `.env.local` (gitignored; `.env` is policy-reserved). Run `python scripts/smoke_qwen.py text` (cheap) or `all` (creates a video task).
