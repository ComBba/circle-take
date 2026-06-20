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

Qwen Cloud, Qwen visual understanding, Wan / HappyHorse video generation, FastAPI, Python, Alibaba Cloud, object storage, JSON schemas, [FILL frontend stack].

## Repository URL

[FILL: public GitHub repo URL]

## Demo Video URL

[FILL: public YouTube/Vimeo/Youku URL, under 3 minutes]

## Live Demo / Testing URL

[FILL: deployed testing URL]

## Testing Instructions

1. Open the demo URL.
2. Use the default golden path brief: `The Last Alarm`.
3. Click `Run Circle Take`.
4. Review Contracts, Storyboard Slate, Take 1, Continuity Court verdict, Reshoot Spell, Take Two Reveal, and Red-Thread Memory.
5. No paid account is required for judges. If login is enabled, use: `[FILL credentials]`.

## Alibaba Cloud Deployment Proof

[FILL: link to code file in repo showing Alibaba Cloud services/APIs used]

## Architecture Diagram

[FILL: link to architecture diagram file in repo]

## License

[FILL: MIT / Apache-2.0]
