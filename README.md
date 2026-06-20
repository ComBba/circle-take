# Circle Take

**Bad takes don't make the cut.**

Circle Take is a self-correcting production loop for generated episodes. It catches broken continuity, reshoots only the failed shot, and remembers only approved takes. Powered by Qwen Cloud.

## Track

Global AI Hackathon Series with Qwen Cloud - Track 2: AI Showrunner

## Golden Path

1. Brief: `The Last Alarm`
2. Generate Actor / Style / Story Contracts
3. Create 4-shot Storyboard Slate
4. Generate Take 1
5. Detect: Luna's red ribbon is missing and the alarm clock became digital
6. CUT
7. Qwen Continuity Court returns verdict JSON
8. Reshoot Shot 2 only
9. Anchor Gate approves Take Two
10. Red-Thread Memory stores story + visual anchors
11. Auto Greenlight proposes Episode 2 cold open

## Architecture

See `docs/architecture.md` and `docs/architecture.png`.

## Qwen Cloud Usage

- Qwen structured output for contracts and storyboards
- Qwen visual/video understanding for Continuity Court
- Wan / HappyHorse T2V, R2V, I2V for generation routes
- Wan / HappyHorse VideoEdit for targeted repair

## Running Locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload
```

## Environment Variables

See `.env.example`.

## License

MIT. Replace if your team chooses another OSI-approved license.

## Deployment Proof

See `deployment/alibaba_cloud_proof.md` and `deployment/alibaba_cloud_services.py`.
