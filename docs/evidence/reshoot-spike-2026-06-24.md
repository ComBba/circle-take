# Reference-Conditioned Reshoot — Live De-Risk Spike (2026-06-24)

**Question:** does a *reference-conditioned* reshoot actually clear the Anchor Gate
(vs. the old blind-t2v reshoot that scored 15/100 and was quarantined)?

**Answer: YES.** Empirical, on real Alibaba Cloud Model Studio (Qwen + Wan), free tier.

## Method
1. Generated a locked **Luna reference keyframe** via free-tier image gen (`wan2.6-t2i`).
2. **Reshoot** via **i2v conditioned on that reference** (`wan2.6-i2v-flash`, 5s @720P, free tier).
3. Extracted a frame and ran the real **Anchor Gate** (Qwen vision, `qwen3.7-plus`) against
   Luna's Actor Contract + Style Contract.

## Result
```
GATE scores = {identity_score: 95, style_score: 95, prop_score: 95, anchor_status: "approved"}
worst = 95   threshold = 85   PASS = True
```

| Reshoot | Anchor Gate | Outcome |
|---|---|---|
| OLD — blind t2v (no identity lock) | 15 / 100 | quarantine (dead-end) |
| NEW — reference-conditioned i2v | **95 / 95 / 95** | **approved → greenlit** |

## Conclusion
The Identity-Lock reshoot (Lever 2) is validated end-to-end on free-tier models. The
fallback ladder (i2v → r2v → kf2v) + honest quarantine remain the safety net, but the
common case now **lands a pass**. Models are env-tunable; production can move to the
latest `wan2.7-i2v` (unified `media[]`) — the concept is proven with `wan2.6-i2v-flash`.

Cost: 1 free-tier image + ~5s free-tier i2v + one vision call.
