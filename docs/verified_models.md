# Verified Models

Status legend: ✅ live-200 confirmed (Task 0.2) · 📄 doc-verified only (pending live) · ❓ candidate

> Fill the ✅ column by running `python scripts/smoke_qwen.py` in Task 0.2 (needs QWEN_API_KEY).
> Only models that return HTTP 200 from the intl endpoint get promoted to "chosen".

## Chosen (to lock in Task 0.2)
| Role | Chosen model | Status | Notes |
|---|---|---|---|
| Text reasoning / contracts | `qwen3.7-plus` | 📄 | GA 2026-06-01, low-cost multimodal agent model |
| Heavy reasoning (optional) | `qwen3.7-max` | 📄 | GA 2026-05-19, 1M context (use only if needed) |
| Vision / Continuity Court | `qwen3.7-plus` | 📄 | multimodal incl. vision/video understanding |
| Video T2V (establishing) | `wan2.7-t2v` | 📄 | Wan 2.7 suite, released 2026-04 |
| Video I2V (first/last frame) | `wan2.7-i2v` | 📄 | |
| Video R2V (character-critical) | `wan2.7-r2v` | 📄 | reference-to-video |
| Video edit (reshoot 1순위) | `wan2.7-videoedit` | 📄 | instruction-based editing |

## Endpoint / auth (doc-verified)
- Host: `https://dashscope-intl.aliyuncs.com`
- Chat (text/vision): `POST /compatible-mode/v1/chat/completions`
- Video: `POST /api/v1/services/aigc/video-generation/video-synthesis` (`X-DashScope-Async: enable`) → poll `GET /api/v1/tasks/{task_id}` (1–5 min)
- Auth: `Authorization: Bearer $QWEN_API_KEY`

## Smoke test results (paste Task 0.2 output here)
```
(pending — run scripts/smoke_qwen.py)
```
