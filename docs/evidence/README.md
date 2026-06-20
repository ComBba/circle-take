# Live Evidence (real Qwen Cloud output)

Proof that Circle Take's pipeline runs on real Qwen Cloud, not fixtures.

- `continuity_verdict_real.json` — a **real Continuity Court verdict** produced by
  `qwen3.7-plus` (vision) judging an actual `wan2.7-t2v`-generated clay-cat frame.
  The model independently detected continuity drift (missing fixed markers) and
  returned a structured repair action. Generated 2026-06-21.

Pipeline proven end-to-end: Wan 2.7 text-to-video (task create→poll→mp4) →
ffmpeg frame → Qwen 3.7 vision verdict. See `docs/verified_models.md`.
