# Demo "Intentional Failure" Strategy (Risk #0)

**Status: 🟡 PENDING USER CONFIRMATION** (recommended default = Option B)

The demo hinges on Take 1 *breaking continuity* (Luna's red ribbon vanishes; alarm-clock
paper dial → digital) and Take Two *restoring* it. Real video models will NOT deterministically
drop-then-restore a specific marker on command. The pack's own risk table ranks "Demo looks
staged" as the #1 risk, so this must be decided before generation.

## Options
- **(A) Genuine generate → genuine detect.** Generate Take 1 with a ribbon-weakening prompt and
  hope the model drops it; Continuity Court catches it for real. Strongest narrative, but low control —
  may need many regenerations (cost/time).
- **(B) Transparently constructed (RECOMMENDED).** Generate two real clips — a "with-ribbon" and a
  "without-ribbon" variant — present them as Take 1 (fail) / Take Two (fixed), and **state the
  construction method openly** in the video + README. Honest, controllable, and the
  Continuity Court verdict is still produced by a **real Qwen-vision call** on the real frame.
- **(C) FORBIDDEN.** Silent staging (hand-edited JSON / fake verdict) — violates the honesty DoD.

## Non-negotiable regardless of A/B
- At least one **real** verdict JSON from an actual Qwen-vision call on a real frame (DoD).
- No silently faked artifacts. If constructed (B), disclose it.

## Decision
- [ ] Option A
- [ ] Option B (recommended)
- Chosen prompts locked in `examples/golden_path/` once decided.
