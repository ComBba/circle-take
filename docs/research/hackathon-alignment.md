# Hackathon Alignment — Global AI Hackathon Series with Qwen Cloud

Sources: https://qwencloud-hackathon.devpost.com/ · /rules · /resources (fetched 2026-06-21).

## Facts
- **Track:** Track 2 — **AI Showrunner** (5 tracks: MemoryAgent, AI Showrunner, Agent Society, Autopilot Agent, EdgeAgent).
- **Deadline:** **2026-07-09 14:00 PDT** (submission window opened 2026-05-26). No late policy.
- **Sponsor/Admin:** Alibaba Cloud / Devpost. Prizes $70K+ across tracks.
- **API:** OpenAI-compatible, base `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` (official resources).
- **Judging weights:** Innovation & AI Creativity 30% · Technical Depth & Engineering 30% · Problem Value & Impact 25% · Presentation & Documentation 15%.

## Required deliverables → Circle Take status
| Requirement | Status | Evidence |
|---|---|---|
| Public OSS repo + license (visible) | ✅ | `ComBba/circle-take` (public), MIT `LICENSE` |
| Text description of features | ✅ | `docs/devpost_submission.md` (English, 7 sections) |
| **Proof of Alibaba Cloud deployment (code file using service/API)** | ✅ | `backend/app/oss_storage.py` (real `oss2` uploads to `circle-take-media`) |
| Architecture diagram | ✅ | `docs/architecture.png` (frontend/backend/Qwen/storage/DB) |
| Demo video <3 min on YouTube/Vimeo/Youku | ⏳ | user records per `docs/demo_script.md` after live UI |
| Track identified | ✅ | Track 2 throughout |
| Testing link or build, free until judging | ⏳ | **local Docker** (`docker compose up`, free) + repo; optional free tunnel for a public URL |

## Track 2 mapping (official ask → evidence)
| Track 2 needs | Circle Take |
|---|---|
| Scriptwriting | `contracts.build_story_contract` (Qwen) → hook/conflict/reversal/button |
| Storyboarding | `storyboard.build_storyboard` + shot-risk ledger (Qwen) |
| Video generation | `video_tasks` → Wan 2.7 (t2v live-proven; i2v/r2v/videoedit routes) |
| Editing | Reshoot Spell → `wan2.7-videoedit` / R2V regeneration fallback |
| Agent autonomy | Scripty: hook→route→verdict→repair→memory→next cold open |
| Multimodal orchestration | Qwen-vision Continuity Court + Anchor Gate on real frames |
| Token budget | compact contracts, delta repair prompts, idempotent runner |

## Differentiator (Innovation 30% + Technical 30%)
Not a video generator — a **self-correcting production loop**: generate → **Qwen judges (real verdict)** → reshoot only the failed shot → store only approved anchors as memory. Proven live (`docs/evidence/continuity_verdict_real.json`).

## Cost posture (per user directive: minimal/free)
- Compute/deploy: **local Docker** (free) instead of paid ECS.
- Storage: OSS pay-as-you-go, tiny footprint; hackathon credits cover Qwen/Wan usage.
- Video: minimize Wan calls; runner reuses generated clips (idempotent).
