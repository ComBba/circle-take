# Demo Video — Upload Kit (ready to publish)

The demo video is **already produced** — fully automated, no human recording.
Your only remaining steps are **upload + paste the URL into Devpost**.

## The file

- **`artifacts/demo/circle-take-demo.mp4`** — 1920×1080, 30 fps, AAC stereo, ~108 s (< 3:00 cap).
- Thumbnail: **`docs/screenshots/demo_thumbnail.png`** (1280×720).
- 100% real: live UI screenshots + the real Wan clips (`take1/take2_S02.mp4`) + the real
  Qwen `VERDICT: FAIL` + the honest Anchor Gate `identity 15/100 → QUARANTINE`.
  Narration is macOS `say` (Samantha) — no microphone, no copyrighted audio.

To regenerate (after any UI change): start the server, then
`node scripts/demo/capture.mjs && python3 scripts/demo/build_demo.py`.

## Upload (YouTube — recommended)

1. studio.youtube.com → **Create → Upload videos** → pick `circle-take-demo.mp4`.
2. **Visibility: Unlisted** (or Public). Both satisfy the rule; Unlisted keeps it judge-only.
3. Upload `docs/screenshots/demo_thumbnail.png` as the custom thumbnail.
4. Copy the title / description / tags below.
5. Copy the resulting watch URL → paste into Devpost **Video** field and into
   `docs/devpost_submission.md` → "Demo Video URL".

> Rule check: the video **must** be on YouTube / Vimeo / Youku and public-or-unlisted —
> a raw file link or Loom/Facebook does not qualify.

### Title
```
Circle Take — Bad takes don't make the cut (Qwen Cloud Hackathon · Track 2: AI Showrunner)
```

### Description
```
Circle Take is a self-correcting episode production loop built on Qwen Cloud.
It catches broken continuity, reshoots ONLY the failed shot, and remembers ONLY approved takes.

In this run (live, unedited logic):
• Take 1 of a clay micro-drama breaks — Luna loses her yellow bead eyes, crescent chest patch, and red collar.
• The Continuity Court (Qwen vision) returns a real VERDICT: FAIL with the exact violations.
• A delta-only Reshoot Spell regenerates shot 2 — and nothing else.
• Take 2 hits the Anchor Gate and scores identity 15/100 → QUARANTINE.
  Circle Take refuses to greenlight an anchor that doesn't match — even its own reshoot.
• Only approved anchors become memory; the failure becomes a rule for the next episode.

Built on: Qwen Cloud (qwen3.7-plus text + vision), Wan 2.7 video generation (T2V/I2V/R2V/VideoEdit),
Alibaba Cloud OSS, FastAPI, Python 3.12, Docker.

Repo: https://github.com/ComBba/circle-take
Track 2 — AI Showrunner · Global AI Hackathon Series with Qwen Cloud
```

### Tags
```
qwen, qwen cloud, alibaba cloud, wan, ai video, ai showrunner, generative video,
continuity, multi-agent, hackathon, devpost, circle take, fastapi, python
```

### Category
`Science & Technology`

## Vimeo / Youku alternative

Same file, same metadata. Set privacy to **Anyone with the link** (Vimeo) or Public (Youku).
Paste the resulting URL into the same two places.
