# Demo Recording Runbook (&lt; 3 minutes)

## Automated path (recommended — no human, no mic, no OBS)

The video is produced end-to-end by scripts. Every frame is real (live-UI screenshots +
the real Wan clips), narration is macOS `say` TTS, captions/cards are burnt in by ffmpeg.

```bash
cd circle-take
docker compose up --build          # or run backend on :8000 (APP_ENV=live, .env.local present)
node scripts/demo/capture.mjs      # stills of every golden-path stage -> build/shots
node scripts/demo/capture_motion.mjs  # real motion (3D hero, scroll montage) -> build/motion
node scripts/demo/capture_live.mjs    # real operation: interactive click + live-run terminal
python3 scripts/demo/build_demo.py    # TTS + ffmpeg (Ken Burns + crossfades) -> artifacts/demo/
python3 scripts/demo/qc.py            # objective gate: 1080p / <=180s / -14 LUFS / no black
```

Audio is loudness-normalized to **-14 LUFS / -1 dBTP** (2-pass loudnorm) and video is CRF 16
— conventions adopted from `Two-Weeks-Team/demo-forge`'s guardrails. `qc.py` exits non-zero on
any failed check (resolution, duration, loudness, true-peak, mid-roll black).

Output: `artifacts/demo/circle-take-demo.mp4` (~165 s, cinematic). Upload per `docs/demo_youtube_kit.md`.
Requires: ffmpeg, Node + a Chrome/Chromium. **Narration uses Qwen Cloud TTS** (`qwen3-tts-flash`)
— needs `QWEN_API_KEY` (read from `.env.local`); falls back to macOS `say` if absent.
Override voice/model via `QWEN_TTS_VOICE` / `QWEN_TTS_MODEL`. Story arc = **live/honest**
(Anchor Gate quarantines Take 2 at identity 15/100 — that refusal is the point).

## Manual path (human voiceover, OBS)

Everything is built and live-verified. This maps the 3-minute script to the **actual live UI**
so you can record in one pass. Pairs with `docs/demo_script.md` (narration).

## 0. Setup (once)
```bash
cd circle-take
# Live (real Wan clips + real Qwen verdict; Anchor Gate is honest = quarantine):
docker compose up --build            # .env.local present -> APP_ENV=live
# — or — clean "approved" narrative (emoji before/after, gate=approved):
APP_ENV=fixture docker compose up --build
```
- Open `http://localhost:8000/ui`, screen-record at 1080p.
- **Pre-run once** (click *Run Circle Take*) so the videos are cached and play instantly on the take.
- Keep the window at the default width; the CUT card and verdict JSON should be readable.

## Which mode?
- **Live** = strongest proof (real generated clips + real verdict), but the Anchor Gate honestly
  quarantined Take 2 (gen didn't fully match Luna's markers) — narrate it as *"the gate is strict;
  it refuses anchors that don't match."* That's a feature, not a bug.
- **Fixture** = the clean PRD narrative (Take Two approved → memory). Use if you want the textbook arc.
- Either way the **Continuity Court verdict is real** in live mode (`docs/evidence/golden-path/`).

## Beat-by-beat (record the single "Run Circle Take" pass, then narrate)
| Time | On screen (UI stage) | Say |
|---|---|---|
| 0:00–0:10 | **Take 1** clip plays (real Wan) | "Luna lost her red ribbon. The alarm clock changed identity." |
| 0:10–0:18 | **CUT** card (big red) | "Circle Take does not hide bad takes." |
| 0:18–0:30 | **Continuity Court** verdict JSON | "Qwen judges the take against the contracts — only the failed shot goes back." |
| 0:30–0:50 | Title / one-liner | "Circle Take is a self-correcting production loop. Catch, reshoot only what failed, remember only approved takes." |
| 0:50–1:15 | **Contracts** cards (Luna, Alarm Clock, Worker) | "Scripty turns a brief into Actor, Style, and Story contracts." |
| 1:15–1:40 | **Storyboard + Shot Risk** (S02 high) | "It scores identity risk — Shot 2 is high because the tail hides the ad and the ribbon can vanish." |
| 1:40–2:05 | **Take 1** + route | "Character-critical shots use references; repairable failures use edit/regeneration." |
| 2:05–2:35 | **Reshoot Spell** (Shot 2 only) | "A delta-only repair instruction for the failed shot." |
| 2:35–2:50 | **Take Two Reveal** (before/after videos) | "The rest of the episode is preserved. Only the broken shot gets a Take Two." |
| 2:50–3:00 | **Memory + Auto Greenlight** | "Only approved takes become memory. Episode 2 starts from what the show remembers." |

## After recording
1. Trim to **under 3:00**; first 30s = the CUT ritual.
2. **Royalty-free music only** (no copyrighted tracks — submission rule).
3. Upload **public/unlisted** to **YouTube / Vimeo / Youku** (not Loom/Facebook).
4. Paste the URL into `docs/devpost_submission.md` → "Demo Video URL" (the last `[FILL]`).
5. Submit on Devpost (Track 2). Re-check `docs/validation_checklist.md` "Hard No-Go".
