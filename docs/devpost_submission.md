# Devpost Submission Draft - Circle Take

> Fill placeholders marked with `[FILL]` before submission.

## Project Title

Circle Take: Bad Takes Don't Make the Cut

## Elevator Pitch

Circle Take is a self-correcting production loop for generated episodes. It catches broken continuity, reshoots only the failed shot, and remembers only approved takes. Powered by Qwen Cloud.

## Track

Track 2 - AI Showrunner

## What It Does

Circle Take turns a short drama brief into a supervised episode workflow. It creates Actor, Style, and Story Contracts; builds a storyboard slate; generates video with Wan / HappyHorse; uses Qwen to judge continuity failures; reshoots only the broken shot; and stores approved story and visual anchors as memory for the next episode.

The signature demo shows Luna, a fictional black cat, losing her required identity markers (red ribbon, yellow clay eyes, crooked left ear) while a broken alarm clock drifts. Circle Take yells CUT, runs a real Qwen Continuity Court verdict (VERDICT: FAIL), then **Scripty — an agent — picks a repair route and reshoots Shot 2 conditioned on a locked reference keyframe (Identity-Lock)**. The Anchor Gate, a real Qwen-vision check rather than a rubber stamp, then scores the reshoot: in a live free-tier run the reference-conditioned reshoot scored **identity/style/prop 95/95/95 → approved**, versus a blind text-only reshoot that scored 15/100 and was quarantined ([evidence](https://github.com/ComBba/circle-take/blob/main/docs/evidence/reshoot-spike-2026-06-24.md)). Only an approved take becomes Red-Thread Memory; when the gate can't verify a take, Circle Take escalates to the next route or honestly quarantines it. The tagline: reshoot the shot, not the show.

## Inspiration

Most AI video tools can generate a clip. Creators need repeatable episodes where characters, props, style, relationships, and unresolved threads survive across shots and episodes. Circle Take was inspired by the film-set idea of a circle take: only approved takes make it into the production record. Bad takes do not make the cut.

## How We Built It

Circle Take is built as an agentic production pipeline on Qwen Cloud.

1. Scripty, the showrunner agent, converts the user brief into Actor, Style, and Story Contracts.
2. The Storyboard Slate creates 3-5 shots and a Shot Risk Ledger.
3. A Generation Route Selector (`video_router`) picks the Wan mode per shot: Take 1 is t2v, and the reshoot uses an escalating **reference-conditioned ladder** (i2v → r2v → kf2v) that locks identity onto a reference keyframe.
4. Wan / HappyHorse generates the episode shots.
5. Qwen visual understanding reviews the generated take against the contracts.
6. Continuity Court returns a structured verdict JSON.
7. Scripty (a Qwen-driven agent) reads the verdict and **chooses the reshoot route**, with its reasoning recorded; a delta-only Reshoot Spell + the reference keyframe regenerate only the failed shot.
8. Anchor Gate (Qwen vision) scores the corrected take and drives **approve / escalate (next route) / honest quarantine**.
9. Red-Thread Memory stores story facts and approved visual anchors for the next episode.

## Qwen Cloud Usage

- Qwen reasoning and structured output for Actor/Style/Story Contracts.
- Qwen visual/video understanding for Continuity Court verdicts.
- HappyHorse / Wan T2V for short video generation.
- HappyHorse / Wan R2V for character-critical shots with references.
- HappyHorse video-edit / Wan videoedit for targeted repair.
- Compact contracts and delta repair prompts to control token budget.

## What Makes It Different

Circle Take is not another video generator. It adds a production memory and correction layer around generation:

- It does not trust the first generation.
- It checks the take against contracts.
- It repairs only the broken shot.
- It quarantines failed keyframes.
- It stores only approved visual anchors as memory.

The key moment is simple: the show stops itself, Qwen judges the mistake, the broken shot gets a Take Two, and only the approved take becomes memory.

## Challenges We Ran Into

- Character identity can drift across generated shots, especially when props occlude an actor.
- Prompt repetition is not enough for consistency, so we added Actor Contracts, Reference Packs, Anchor Slates, and Anchor-Gated Memory.
- Targeted repair can fail, so the repair path falls back from VideoEdit to R2V regeneration and then shot rewrite.
- The demo had to explain the full loop in under three minutes, so we focused on one golden path instead of broad feature coverage.

## Accomplishments That We're Proud Of

- Designed a memorable first-30-second demo around the CUT ritual.
- Built a showrunner pipeline that includes scriptwriting, storyboarding, generation, editing, review, repair, and memory.
- Created an Identity Lock Stack that goes beyond prompt repetition.
- Turned visual continuity into a judgeable artifact: verdict JSON, repair prompt, before/after reveal, and approved memory.

## What We Learned

We learned that generated video workflows need production supervision, not just better prompts. A useful showrunner must remember what should persist, detect when it breaks, and decide what gets approved for the next episode.

## What's Next

- Add more Style Contracts after the Clay Stop-Motion MVP.
- Expand Reference Pack creation and approval tools.
- Improve shot-level repair routing and cost controls.
- Add open-source examples for creators to define their own fictional actors.
- Extend Red-Thread Memory across multiple generated episodes.

## Built With

Alibaba Cloud Model Studio (DashScope) — Qwen3.7 (text + vision) and Wan/HappyHorse video (t2v, and reference-conditioned i2v/r2v/kf2v for the Identity-Lock reshoot); Alibaba Cloud OSS (oss2); FastAPI, Python 3.12, Pydantic v2, SQLite, Docker, vanilla HTML/CSS/JS demo UI, JSON schemas.

## Repository URL

https://github.com/ComBba/circle-take

## Demo Video URL

https://youtu.be/QZrLzBsiJbo

(1080p, ~2:23, < 3:00. Set visibility to Public or Unlisted before submitting.)

## Live Demo / Testing URL

**Live (running on Alibaba Cloud ECS):** http://43.98.203.221:8000/ui/ — Singapore `ap-southeast-1`.
HTTPS mirror: https://circle-take-145226765474.us-central1.run.app/ui/

The backend is **deployed and running on Alibaba Cloud ECS** (instance `circletake-proof`, Docker
Compose) in fixture mode (deterministic golden path, no credentials, no per-request cost). It uses
Qwen Cloud (DashScope) + Alibaba Cloud OSS at runtime in live mode — Alibaba deployment proof:
`backend/app/alibaba_cloud_integration.py` + `deployment/alibaba_cloud_proof.md`.

Or run free locally:
```bash
git clone https://github.com/ComBba/circle-take && cd circle-take
docker compose up --build      # -> http://localhost:8000/ui
```

## Testing Instructions

1. `docker compose up --build`, then open `http://localhost:8000/ui` (fixture mode — no credentials, no cost).
2. The default brief `The Last Alarm` is preloaded; click **Run Circle Take**.
3. Watch the full golden path: Contracts → Storyboard (S02 high-risk) → Take 1 → **CUT** → Continuity Court verdict JSON → Reshoot Spell → Take Two → Anchor Gate → Red-Thread Memory → Auto Greenlight.
4. No login or paid account required. For the *live* run on real Qwen3.7 + Wan2.7 + OSS, see `docs/evidence/golden-path/` and `deployment/local-docker.md`.

## Alibaba Cloud Deployment Proof

**Backend deployed & running on Alibaba Cloud ECS** — instance `i-t4n9vck3xkdijyhfxeb3`
("circletake-proof"), `ecs.e-c1m2.large`, region `ap-southeast-1` (Singapore), reachable at
`http://43.98.203.221:8000` (`/health` → 200). Console screenshot: `docs/screenshots/alibaba-deployment.png`.

Code proof: https://github.com/ComBba/circle-take/blob/main/backend/app/alibaba_cloud_integration.py
— Qwen + Wan run on **Alibaba Cloud Model Studio (DashScope, `dashscope-intl.aliyuncs.com`)** and
generated media is stored on **Alibaba Cloud OSS** (`oss2`, bucket `circle-take-media`). Run
`python -m app.alibaba_cloud_integration` to print the services manifest.

## Architecture Diagram

https://github.com/ComBba/circle-take/blob/main/docs/architecture.png

## License

MIT — https://github.com/ComBba/circle-take/blob/main/LICENSE
