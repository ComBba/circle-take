# Local Docker (free) + testing link

A zero-cost path to a working demo / judge testing link — no paid cloud required.

## Fixture mode — recommended for the public testing link (safe, free, no creds)
```bash
docker compose up --build          # no .env.local present -> APP_ENV=fixture
# open http://localhost:8000/ui  — walks the full golden path on documented fixtures
```
Safe to expose publicly: **no credentials, no API cost, deterministic.** For a public URL
without a server, use a free tunnel:
```bash
cloudflared tunnel --url http://localhost:8000     # or: ngrok http 8000
```

## Live mode — local demo only (real Qwen3.7 + Wan2.7 + OSS)
Requires `.env.local` (sets `APP_ENV=live` + creds) and a prior live run
(`python scripts/run_golden_path_live.py all`, which fills `artifacts/live/`):
```bash
docker compose up --build          # .env.local -> APP_ENV=live; artifacts/live mounted read-only
# /ui shows the REAL contracts, Continuity Court verdict, and Anchor Gate
```
**Do not expose the live container publicly** — it carries credentials and incurs API cost.
Demonstrate live via the demo video + `docs/evidence/` + OSS objects.

## Verified (2026-06-21)
Container live mode confirmed: `/health` → `mode: live`; full golden path → real verdict
(`fail`, 3 violations); real Qwen actors (`Luna`, `Broken Alarm Clock`, `Arthur`); `/ui` → 200.
Image: `python:3.12-slim`, non-root, healthcheck. Build verified with Docker 29.5.2.
