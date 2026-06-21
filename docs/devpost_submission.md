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

The signature demo shows Luna, a fictional black cat, losing her required red ribbon while a broken alarm clock drifts from a paper dial to a digital screen. Circle Take yells CUT, runs a Qwen Continuity Court verdict, reshoots Shot 2 only, approves the corrected take, and stores the approved visual anchor in Red-Thread Memory.

## Inspiration

Most AI video tools can generate a clip. Creators need repeatable episodes where characters, props, style, relationships, and unresolved threads survive across shots and episodes. Circle Take was inspired by the film-set idea of a circle take: only approved takes make it into the production record. Bad takes do not make the cut.

## How We Built It

Circle Take is built as an agentic production pipeline on Qwen Cloud.

1. Scripty, the showrunner agent, converts the user brief into Actor, Style, and Story Contracts.
2. The Storyboard Slate creates 3-5 shots and a Shot Risk Ledger.
3. A Generation Route Selector chooses between T2V, R2V, I2V, and VideoEdit routes.
4. Wan / HappyHorse generates the episode shots.
5. Qwen visual understanding reviews the generated take against the contracts.
6. Continuity Court returns a structured verdict JSON.
7. Reshoot Spell creates a delta-only repair instruction for the failed shot.
8. Anchor Gate approves or quarantines the corrected take.
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

Qwen Cloud (qwen3.7-plus text + vision), Wan 2.7 video generation (T2V/I2V/R2V/VideoEdit), FastAPI, Python 3.12, Pydantic v2, Alibaba Cloud OSS (oss2), SQLite, Docker, vanilla HTML/CSS/JS demo UI, JSON schemas.

## Repository URL

https://github.com/ComBba/circle-take

## Demo Video URL

Video is **already produced**: `artifacts/demo/circle-take-demo.mp4` (1080p, ~108 s, < 3:00).
Upload it to YouTube/Vimeo/Youku per `docs/demo_youtube_kit.md` (title/description/tags ready),
then replace this line with the watch URL.

[FILL: paste the public YouTube/Vimeo/Youku URL here after upload]

## Live Demo / Testing URL

Run free locally (no account, no paid cloud):
```bash
git clone https://github.com/ComBba/circle-take && cd circle-take
docker compose up --build      # -> http://localhost:8000/ui
```
[Optional public URL: `cloudflared tunnel --url http://localhost:8000` — FILL with the tunnel URL if used.]

## Testing Instructions

1. `docker compose up --build`, then open `http://localhost:8000/ui` (fixture mode — no credentials, no cost).
2. The default brief `The Last Alarm` is preloaded; click **Run Circle Take**.
3. Watch the full golden path: Contracts → Storyboard (S02 high-risk) → Take 1 → **CUT** → Continuity Court verdict JSON → Reshoot Spell → Take Two → Anchor Gate → Red-Thread Memory → Auto Greenlight.
4. No login or paid account required. For the *live* run on real Qwen3.7 + Wan2.7 + OSS, see `docs/evidence/golden-path/` and `deployment/local-docker.md`.

## Alibaba Cloud Deployment Proof

https://github.com/ComBba/circle-take/blob/main/backend/app/oss_storage.py
(also `deployment/alibaba_cloud_services.py`) — real `oss2` SDK usage uploading generated
videos/keyframes/verdicts to OSS bucket `circle-take-media`.

## Architecture Diagram

https://github.com/ComBba/circle-take/blob/main/docs/architecture.png

## License

MIT — https://github.com/ComBba/circle-take/blob/main/LICENSE
