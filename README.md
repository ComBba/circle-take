# Circle Take

[![CI](https://github.com/ComBba/circle-take/actions/workflows/ci.yml/badge.svg)](https://github.com/ComBba/circle-take/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

**Bad takes don't make the cut.**

▶️ **Live demo:** https://circle-take-145226765474.us-central1.run.app/ui/ · 🎬 **Video:** https://youtu.be/QZrLzBsiJbo

Circle Take is a self-correcting production loop for generated episodes. It catches broken continuity, reshoots only the failed shot, and remembers only approved takes. Powered by Qwen Cloud.

**Track:** Global AI Hackathon Series with Qwen Cloud — Track 2: AI Showrunner
**License:** MIT

## Status

Anyone can **watch the full loop** with no account. To run **your own** live episode,
bring your own Qwen key (BYOK) — it stays in your browser and powers real Qwen3.7 +
Wan 2.7 generation. Nothing is stored server-side.

| Area | State |
|---|---|
| Orchestrator (state machine + endpoints) | ✅ pytest green, verified in Docker |
| Public Watch-the-loop demo (no key, no account) | ✅ `GET /api/demo` golden path + presigned clips |
| BYOK live: per-request Qwen key (`X-Qwen-Key`) | ✅ used per request, never stored or logged |
| Live Qwen3.7 contracts / Continuity Court | ✅ real Qwen-vision verdict from the generated frame |
| Live Wan video gen (async per request) | ✅ create→poll; serves the caller's own DashScope URL |
| **Generation-route selector + reference-conditioned reshoot (Identity-Lock)** | ✅ i2v/r2v/kf2v ladder on a locked keyframe — **live-proven 95/95/95 → approved** (vs blind-t2v 15/100), [evidence](docs/evidence/reshoot-spike-2026-06-24.md) |
| **Agentic Scripty (Qwen-driven repair decision)** | ✅ picks the reshoot route + records its reasoning |
| **Capped judge-live path** (judges run live without their own key) | ✅ BYOK > judge-cap > fixture; judge key never stored or returned |
| Storage | ✅ none — no accounts, no keys; ephemeral SQLite |
| Deploy (Cloud Run, single instance) | ✅ `deployment/cloud_run_deploy.md` |

> **How "live" works (honest):** watching the loop is public and key-free. To generate your own
> episode, you pass a Qwen key via `X-Qwen-Key` (kept only in your browser). The server uses it
> **only for that request** — never stored or logged — to make real per-request calls: Qwen3.7 for
> contracts/storyboard, Wan 2.7 for Take 1/Take 2 (async, 1–5 min, polled via `/take/{n}/poll`),
> and Qwen3.7-vision for the Continuity Court verdict on the actual generated frame. The Anchor
> Gate returns `quarantine` when a take doesn't match the contracts — strict, not a rubber stamp.
> With no key, the endpoints replay golden-path fixtures (never presented as live output).

## Demo

The self-contained UI (served at `/ui`) walks the full golden path in the browser — the **CUT** moment is the centerpiece:

![Circle Take golden-path demo UI](docs/screenshots/golden-path.png)

## Golden Path

`Brief → Contracts → Storyboard → Take 1 → CUT → Continuity Court verdict → Reshoot (Shot 2 only) → Take Two → Anchor Gate → Red-Thread Memory → Auto Greenlight (Episode 2: "The Delivery Box")`

The signature failure: Luna's red ribbon disappears in Shot 2 and the alarm clock's paper dial turns digital — Qwen catches it, only Shot 2 is reshot, and only the approved take becomes memory.

## Quickstart

### Docker (recommended)

```bash
docker compose up --build
# → http://localhost:8000/health
```

### Local (Python 3.12)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000
```

### Walk the golden path (BYOK)

```bash
B=http://localhost:8000
# Public, no key — the whole walkthrough in one call:
curl -s $B/api/demo
# Or run your own live episode by passing your Qwen key (used per request, never stored):
H='X-Qwen-Key: sk-...'    # your DashScope key
EID=$(curl -s -X POST $B/api/episodes -H 'content-type: application/json' \
  -d '{"title":"The Last Alarm"}' | python -c "import sys,json;print(json.load(sys.stdin)['episode_id'])")
curl -s -X POST $B/api/episodes/$EID/generate -H "$H"     # -> TAKE_1_READY (live: starts Wan Take 1)
curl -s -X POST $B/api/episodes/$EID/take/1/poll -H "$H"  # poll until take_1.status == succeeded
curl -s -X POST $B/api/episodes/$EID/review   -H "$H"     # -> CUT_REQUIRED (real Qwen-vision verdict)
curl -s -X POST $B/api/episodes/$EID/reshoot  -H "$H"     # -> TAKE_2_READY (starts Wan Take 2)
curl -s -X POST $B/api/episodes/$EID/take/2/poll -H "$H"
curl -s -X POST $B/api/episodes/$EID/memory   -H "$H"     # -> AUTO_GREENLIT
curl -s $B/api/episodes/$EID/report                       # full production report
```

Without `X-Qwen-Key` the endpoints replay golden-path fixtures (no Qwen calls).

### Tests

```bash
cd backend && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q       # 104 passed, 1 skipped (Postgres roundtrip: set TEST_DATABASE_URL)
```

## Qwen Cloud Usage (Alibaba Cloud Model Studio / DashScope)

| Need | Model |
|---|---|
| Contracts / storyboard / **Scripty repair decision** (text) | `qwen3.7-max` / `qwen3.7-plus` |
| Continuity Court + Anchor Gate (vision verdicts) | `qwen3.7-plus` / `qwen3-vl-plus` |
| Take 1 (establishing, intentional drift) | Wan `wan2.7-t2v` (t2v) |
| **Reference-conditioned reshoot (Identity-Lock)** | Wan `wan2.7-i2v` / `wan2.7-r2v` / `wan2.2-kf2v-flash` (conditioned on the locked keyframe) |
| Targeted edit fallback | Wan `wan2.1-vace-plus` (vace) |

The AI runs on **Alibaba Cloud Model Studio (DashScope)**: `dashscope-intl.aliyuncs.com`
(chat: `/compatible-mode/v1`; video: async `video-synthesis` / `image2video` → poll
`/tasks/{id}`). Route selection lives in `video_router.reshoot_ladder`; the mode-aware
submitter is `video_tasks.submit_video`.

## Architecture

```mermaid
flowchart LR
  UI["UI /ui (watch public · BYOK key for live)"] -->|"REST + X-Qwen-Key"| API
  subgraph API["FastAPI orchestrator"]
    EP["episode endpoints (anonymous)"]
    SM["state machine"]
    DB[("ephemeral SQLite")]
    EP --> SM
    EP --> DB
  end
  API --> PIPE["pipeline (live, per request)"]
  PIPE --> QC["qwen_client"]
  PIPE --> VT["video_tasks"]
  QC -->|"qwen3.7-plus chat+vision (caller's key)"| QWEN["Qwen Cloud"]
  VT -->|"wan2.7-t2v create→poll (caller's key)"| WAN["Wan 2.7"]
  API --> DEMO["/api/demo presigned clips"]
  DEMO --> OSS[("Alibaba OSS")]
```

The **AI compute runs on Alibaba Cloud Model Studio** (Qwen + Wan via DashScope) and media is
stored on **Alibaba OSS**; the orchestrator container runs on **Google Cloud Run** (single
instance, ephemeral SQLite — nothing durable) — see
[`deployment/cloud_run_deploy.md`](deployment/cloud_run_deploy.md). Public demo clips are
presigned from the Alibaba OSS bucket.

Full diagrams (system / state machine / live sequence) + `architecture.png` in [`docs/architecture.md`](docs/architecture.md).
State machine: `DRAFT → CONTRACTED → STORYBOARDED → GENERATING → TAKE_1_READY → REVIEWING → CUT_REQUIRED → RESHOOTING → TAKE_2_READY → ANCHOR_APPROVED → REMEMBERED → AUTO_GREENLIT`.

## Environment Variables

See `.env.example`. Model IDs are centralized there. Live runs use the caller's **BYOK** `X-Qwen-Key` per request (a server `QWEN_API_KEY` is only needed for the offline scripts in `scripts/`); `DATABASE_URL` is ephemeral SQLite; the public demo clips are presigned with `ALIBABA_CLOUD_*`.

## Alibaba Cloud Deployment Proof

The single linkable proof file is [`backend/app/alibaba_cloud_integration.py`](backend/app/alibaba_cloud_integration.py)
— it consolidates the two Alibaba Cloud touchpoints (Model Studio / DashScope for Qwen + Wan,
OSS via `oss2`) and prints a services manifest (`python -m app.alibaba_cloud_integration`).
The AI compute runs on Alibaba Cloud Model Studio; generated media is stored on Alibaba OSS.

## License

MIT — see `LICENSE`.
