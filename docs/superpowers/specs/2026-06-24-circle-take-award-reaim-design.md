# Circle Take — Award Re-Aim Design

**Date:** 2026-06-24
**Track:** Qwen Cloud Global AI Hackathon — Track 2 (AI Showrunner)
**Deadline:** 2026-07-09 14:00 PDT (~15 days)
**Repo:** ComBba/circle-take · branch `feat/award-reaim`

**Goal:** Re-aim the existing Circle Take build away from "real public product" decisions and toward the hackathon judging rubric — keeping the CUT self-correcting loop, but making the Identity-Lock Stack mechanically real, the demo payoff land, and the Alibaba Cloud deployment proof airtight.

---

## 1. Why re-aim (evidence)

### 1.1 The rubric (what actually scores)
| Criterion | Weight | What it rewards |
|---|---|---|
| Innovation & AI Creativity | 30% | *"Sophisticated use of Qwen Cloud APIs"* + algorithm/engineering innovation |
| Technical Depth & Engineering | 30% | architecture quality, code cleanliness, stack sophistication |
| Problem Value & Impact | 25% | real-world relevance, scalability |
| Presentation & Documentation | 15% | demo clarity, technical docs |

60% of the score rewards **visible, sophisticated, working Qwen/Wan usage** and **engineering depth**.

### 1.2 The killer finding
`backend/app/video_router.py` (the T2V/I2V/R2V/VideoEdit "Generation Route Selector" — a centerpiece of the PRD and Devpost) **is never imported by `backend/app/pipeline.py`.** Verified:
- `grep -rn video_router backend/app/` → no hit outside the file itself.
- `pipeline.start_take()` and `pipeline.reshoot()` both hardcode `WAN_T2V_MODEL` with a plain text prompt (`FAIL_PROMPT` / `FIX_PROMPT`). No `extra_input`, no reference images, no I2V/R2V.

Consequences:
1. **The Identity-Lock Stack is prose, not pixels.** Nothing mechanically locks Luna's identity into Take 2 — it is an unrelated fresh T2V generation.
2. **That is why the live Anchor Gate scored the reshoot 15/100 and quarantined it.** The demo dead-ends with "nothing got greenlit," which a judge reads as "it doesn't work."
3. **Claim↔code gap.** A judge reading the repo sees the route selector advertised but unused — bleeds both 30% buckets.

### 1.3 Product decisions that cost rubric points (being reversed)
- **Google Cloud Run only** → rules require Alibaba Cloud deployment proof.
- **BYOK + fixture-default** → a judge clicking the live URL sees canned fixtures, not live Qwen.
- **Honest-but-dead-end quarantine** → strong thesis, no satisfying payoff.

### 1.4 Assets to keep untouched
CUT ritual; narrative landing page; schema-validated Qwen JSON client (`qwen_client.py`); clean module structure; real Qwen text stage (`contracts.py`, `storyboard.py` already call Qwen).

---

## 2. Global constraints (apply to every task)

- **Git:** push only to **ComBba** (never TwoWeeksTeam). **No squash merge** — `gh pr merge --merge`; rebase only for conflicts. Feature branches only.
- **Secrets:** only in `.env.local` (gitignored, hook-protected). Never commit; mask in output. Contains `QWEN_API_KEY` (sk-ws-…), `ALIBABA_CLOUD_*` OSS creds.
- **Credits:** building budget is a **~$40 participation coupon** ([qwencloud.com/challenge/hackathon/voucher-application](https://www.qwencloud.com/challenge/hackathon/voucher-application), claim with the registered email) **+ the Track-2 "highest token allowance"** (free per-model quota). The $3,000 cloud credits are a *prize*, post-win — not available now. Therefore: claim the voucher + check the Track-2 token allowance **before** the Lever-2 live spike; live Wan tuning on the owner's key is authorized but kept minimal (spike → confirm → build with fixtures → final live verification only). Wan video is the dominant cost; the DashScope key exposes **no balance endpoint** — balance is read only via the console.
- **Any Google Cloud Run cleanup/redeploy MUST pass `--project ss-xprize-share-616b`** (active gcloud project drifts to `ss-memory-os`).
- **No fabricated live results.** Live = real API or explicitly fixture-mode. Every "it works" claim shows observed evidence.
- Commits end with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## 3. Lever-by-lever design

### Lever 1 — Alibaba Cloud deployment proof `[CRITICAL]`

**Verified rule text:** *"You must demonstrate that the backend is running on Alibaba Cloud. Proof must be a link to a code file in their code repo that demonstrates use of Alibaba Cloud services and APIs."*

**Verified facts:** the real-name verification that blocks ECS is **region-triggered (mainland), not service-triggered**. OSS already works → the account can provision non-mainland resources. **Function Compute in Singapore** does not cross the blocked gate. DashScope/Model Studio is officially Alibaba Cloud.

**Three-tier, independently-shippable approach:**

1. **Floor (compliant immediately):** add `backend/app/alibaba_cloud_integration.py` — a single clearly-named module that consolidates and documents the Alibaba Cloud touchpoints already in use: OSS via `oss2` (media storage/presigning) + DashScope/Model Studio calls (Qwen text/vision + Wan video) against `dashscope-intl.aliyuncs.com`. This is the linkable "code file" proof. (It re-exports/wraps existing `oss_storage.py` + `qwen_client.py` + `video_tasks.py` calls — no behavior change, DRY.)
2. **Cheap upgrade:** OSS **Static Website Hosting** for the frontend → a real `*.oss-ap-southeast-1.aliyuncs.com` (or custom-domain) Alibaba public URL. Use a **separate frontend bucket** so the media bucket's private/presigned posture is untouched. Note: raw OSS endpoint forces HTML download; a custom domain (CNAME) renders in-browser — optional.
3. **Airtight:** deploy the FastAPI backend to **Function Compute (Singapore)**. Path A: Custom Container (Dockerfile `--platform linux/amd64` → ACR Personal Edition Singapore → FC HTTP trigger). Path B fallback (if ACR demands the blocked verification): FC **Custom Runtime (Python)**, zip upload, no registry. **Verify-before-spend:** attempt one free ACR Personal Edition instance in Singapore; branch on the result. Backend then literally runs on Alibaba Cloud, matching Alibaba's own first-prize precedent (FC + OSS + Model Studio).

**Architecture diagram** updated to show: Frontend (OSS static hosting) → FC backend (Singapore) → DashScope/Model Studio (Qwen + Wan) → OSS (media).

**Testing:** `alibaba_cloud_integration.py` unit-covered (mocked oss2/httpx) — asserts it targets `aliyuncs.com` endpoints and the `circle-take-media` bucket. Deployment proven by live `curl <FC-url>/health` returning `mode:live` (empirical, recorded in the PR).

---

### Lever 2 — Real route selector + reference-conditioned reshoot + fallback ladder `[engineering headline]`

**The fix that makes the Identity-Lock Stack real and lands the demo payoff.**

**Reference Pack:** lock canonical keyframes for the golden path — Luna (black clay cat, red ribbon, crooked left ear, yellow clay eyes) and the alarm clock (paper dial). Stored as committed reference frames (or generated once and pinned). These are the identity anchors the reshoot conditions on.

**Wire `video_router` into `pipeline`:**
- `start_take(... , shot_meta)` consults `video_router.select_route(shot)` → `models_for(route)` instead of hardcoding T2V.
- **Take 1** = T2V (intentional drift, the constructed golden failure — kept).
- **Reshoot (Take 2)** = **I2V or R2V conditioned on the Reference Pack** via the already-supported `video_tasks.create_task(..., extra_input={...})` (reference image(s) passed to Wan). This genuinely restores the red ribbon + paper dial.
- **Fallback ladder** driven by the Anchor Gate score: `videoedit → r2v regen → (still failing) honest quarantine`. The honest-refusal capability stays real; it's now the *last* resort, not the default outcome.

**Data flow change in `pipeline.reshoot()` / `memory_stage()`:**
```
verdict → reshoot_spell (delta) → select_route(repair=True)
  → Wan I2V/R2V (extra_input=reference frames) → poll → frame
  → Anchor Gate (vision score)
       score ≥ threshold → approve → Red-Thread Memory   [satisfying payoff]
       score <  threshold → escalate next route in ladder
       ladder exhausted    → quarantine (honest refusal)  [still real]
```

**Error handling:** Wan task FAILED/timeout → advance ladder, not raw 500. Threshold is config-tunable (realistic value set empirically in the spike, not aspirational 85).

**Testing:** unit tests for route wiring (`select_route` consulted, `extra_input` populated for reshoot), ladder escalation logic (mock gate scores drive the right next route), and a fixture-mode end-to-end that exercises approve AND quarantine branches. One recorded **live spike** proving a reference-conditioned reshoot actually clears the gate (de-risk gate before full build).

---

### Lever 3 — Agentic Scripty (one genuine Qwen-driven decision) `[innovation headline]`

Turn the linear pipeline into a real agent at the repair step. Instead of a hardcoded ladder order, **Scripty (Qwen) decides the repair strategy** from the verdict + Anchor Gate scores + remaining-route budget, returning a structured decision with reasoning.

- New module `backend/app/scripty.py`: `decide_repair(verdict, gate_history, routes_left) -> RepairDecision` (Qwen structured/JSON via `qwen_client.qwen_json`, schema-validated). Fields: `chosen_route`, `reasoning`, `expected_fix`, `give_up` (bool).
- The pipeline calls `scripty.decide_repair(...)` to pick the next route; the deterministic ladder remains the **fallback/guardrail** if Scripty errors (defensive, not load-bearing).
- **Reasoning is surfaced as an artifact** (`scripty_decisions`) the UI and judges can read — visible agent cognition is the differentiator the rubric rewards.

**Bounded scope:** ONE real agent decision loop, not a multi-agent framework. YAGNI on tool-calling frameworks.

**Testing:** schema validation of `RepairDecision`; fixture test that Scripty's chosen route is honored and that an errored/invalid decision falls back to the deterministic ladder.

---

### Lever 4 — Capped judge live path `[presentation + visible sophistication]`

Server-side judge key so judges see real Qwen+Wan without their own key, cost-bounded.

- Config: optional `JUDGE_QWEN_KEY` (owner's key) loaded server-side. If unset, behavior is today's BYOK/fixture.
- New `backend/app/ratelimit.py`: a simple global counter (SQLite-backed) — **N live judge runs/day** (e.g., 10) and **golden-path brief only** for the free judge run. Beyond the cap → graceful fixture replay + a clear message ("daily live budget reached — bring your own key to run live").
- `main.py` resolves the effective key per request: `X-Qwen-Key` (BYOK) > judge key (if within cap, golden brief) > none (fixture). The judge key is **never** returned, logged, or exposed to the client.
- BYOK and the open-source no-storage story stay intact for "run your own brief."

**Testing:** rate-limit unit tests (cap enforced, resets per day, non-golden brief rejected from judge budget); endpoint test that the judge key never appears in any response; that BYOK still overrides.

---

### Lever 5 — Presentation refresh (15%) `[mostly post-dev]`

- Re-cut <3min demo to land the new payoff (Take 1 drift → CUT → Qwen verdict → reference-conditioned reshoot → **Anchor Gate approves** → memory → auto-greenlight), with the honest-refusal shown as the safety net. *(User re-records after code freeze.)*
- Devpost text: update for the real route selector, agentic Scripty, FC-Singapore Alibaba deployment, judge-live + BYOK paths.
- Architecture diagram: Alibaba services (FC + OSS static + OSS media + Model Studio).
- README: live judge URL + "run your own (BYOK)" + Alibaba proof file link.

---

## 4. De-risk sequence (implementation order)

1. **Alibaba floor** — `alibaba_cloud_integration.py` proof file → compliant immediately.
2. **Lever 2 live spike** — confirm a reference-conditioned reshoot clears the Anchor Gate (the #1 model-reliability risk), owner's key, recorded. **Gate:** if it can't clear, fall back to "honest escalation that eventually passes via strongest route," re-tune threshold, or adjust references before building out.
3. **Lever 2 full** — wire `video_router`, Reference Pack, fallback ladder, tests.
4. **Lever 3** — agentic Scripty + decision artifact + tests.
5. **Lever 4** — capped judge path + rate limit + tests.
6. **Alibaba airtight** — FC Singapore deploy (verify-before-spend ACR → Python-runtime fallback); update architecture diagram.
7. **Lever 5** — Devpost/README/diagram refresh (video re-record is the user's post-dev step).

Each step is independently shippable as its own PR (`--merge`, no squash).

---

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Reference-conditioned reshoot still can't clear the gate reliably | Spike first (step 2). Fallback ladder escalates to strongest route; threshold set empirically; honest quarantine remains valid if truly unfixable. |
| ACR Personal Edition needs the blocked verification | FC Custom Runtime (Python, no ACR) fallback. Verify-before-spend. |
| Live credit burn during tuning | Spike → confirm → build with fixtures; only final verification runs live; judge path rate-limited. |
| FC cold start / timeout on long Wan polls | FC HTTP trigger + async poll pattern already matches; tune FC timeout; keep poll endpoints idempotent. |
| Scope creep (15 days) | YAGNI: one agent decision (not a framework); keep BYOK/landing as-is; presentation is post-dev. |
| gcloud project drift breaks a GCR cleanup | Always `--project ss-xprize-share-616b`. |

---

## 6. Out of scope (YAGNI)

- Multi-agent orchestration framework; tool-calling beyond one structured decision.
- Multi-style support beyond Clay Stop-Motion MVP.
- User accounts / durable multi-tenant storage (BYOK + ephemeral SQLite stays).
- Long-form / multi-episode full rendering.
- Rewriting the narrative landing page or CUT ritual.

---

## 7. Affected files (map)

| File | Change |
|---|---|
| `backend/app/alibaba_cloud_integration.py` | **new** — consolidated Alibaba proof module (wraps oss2 + dashscope calls) |
| `backend/app/pipeline.py` | wire `video_router`; reference-conditioned reshoot; fallback ladder; call `scripty.decide_repair` |
| `backend/app/video_router.py` | now actually imported; possibly add reference-input helpers |
| `backend/app/video_tasks.py` | use `extra_input` for I2V/R2V reference frames |
| `backend/app/scripty.py` | **new** — Qwen-driven repair decision (agentic) |
| `backend/app/anchor_gate.py` | threshold from config; expose score history for ladder |
| `backend/app/ratelimit.py` | **new** — daily judge-run cap (SQLite) |
| `backend/app/main.py` | effective-key resolution (BYOK > judge-cap > fixture); judge key never exposed |
| `backend/app/config.py` | `JUDGE_QWEN_KEY`, gate threshold, daily cap config |
| `frontend/index.html` | judge-live affordance; keep BYOK + landing |
| `deployment/` | FC Singapore deploy (container + Python-runtime fallback) |
| `docs/architecture.*` | Alibaba services topology |
| `docs/devpost_submission.md` | BYOK + judge-live + real route selector + FC proof |
| `backend/tests/` | new/updated tests per lever |
