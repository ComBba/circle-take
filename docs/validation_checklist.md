# Circle Take - 검증 및 제출 체크리스트

**Status (2026-06-21):** engineering complete + live-proven. Remaining = demo video (user) + Devpost submit.
Legend: `[x]` done · `[ ]` pending (mostly video) · ⚠️ note.

## Stage One Pass/Fail

- [x] Track 2로 명확히 식별했다.
- [x] Qwen Cloud API 사용이 코드와 데모에서 보인다. (`qwen_client`, live-verified `qwen3.7-plus`)
- [x] Wan / HappyHorse video generation 또는 editing 계열 사용이 보인다. (`video_tasks`, live `wan2.7-t2v`)
- [x] Scriptwriting, storyboarding, generation, editing이 모두 들어간다.
- [x] 프로젝트가 영상/텍스트 설명과 동일하게 작동한다. (live golden path proven)

## Stage Two Scoring Defense

### Innovation & AI Creativity 30%
- [x] Circle Take가 단순 video generator가 아니라 self-correcting production loop로 설명된다.
- [x] Continuity Court, Reshoot Spell, Anchor Gate, Red-Thread Memory가 보인다.
- [x] Qwen이 planning, route selection, verdict, repair, memory gate에서 쓰인다.
- [ ] CUT ritual이 첫 30초 안에 나온다. (UI/script ready; confirm in demo video)

### Technical Depth & Engineering 30%
- [x] Architecture diagram에 frontend, Alibaba Cloud backend, Qwen Cloud, storage/database가 보인다.
- [x] Repo에 backend orchestrator 코드가 있다. (FastAPI, state machine, 7 endpoints)
- [x] Async video task polling 또는 task state management가 있다. (`video_tasks.poll` + EpisodeStatus)
- [x] Error fallback이 있다: VideoEdit -> R2V regeneration. (`route_selector.models_for`)
- [x] JSON schemas와 golden path artifacts가 repo에 있다.

### Problem Value & Impact 25%
- [x] "repeatable character episode production" 문제로 설명한다.
- [x] Short-form creators / character IP makers가 primary users로 명시된다.
- [x] Approved visual anchors와 story memory가 다음 episode에 이어진다.

### Presentation & Documentation 15%
- [ ] Demo is under 3 minutes. (record per `docs/demo_script.md`)
- [ ] First 30 seconds show the key logic visually. (script ready)
- [x] README has setup instructions. (Docker + local + tests)
- [x] Devpost form is in English.
- [x] Architecture docs are clear.

## Official Submission Requirements
- [x] Public code repository URL. (https://github.com/ComBba/circle-take)
- [x] Open-source license visible at top level. (MIT)
- [x] Text description explaining features/functionality.
- [x] Proof of Alibaba Cloud Deployment (code file). (`backend/app/oss_storage.py` — real OSS uploads)
- [x] Architecture diagram showing Qwen Cloud, backend, storage, frontend.
- [ ] Demo video under 3 minutes, public on YouTube/Vimeo/Youku. (user)
- [ ] Demo video shows project functioning. (user)
- [x] No unauthorized third-party trademarks/music/materials. (original synthetic actors; ⚠️ keep demo music royalty-free)
- [x] Track identified as Track 2.
- [x] Testing link or build available free. (`docker compose up`, fixture mode, no creds)
- [x] English translation/materials available.

## Golden Path Verification (live + UI)
- [x] User brief loads.
- [x] Actor / Style / Story Contract generated. (live Qwen)
- [x] Storyboard Slate generated.  [x] Shot Risk Ledger generated.
- [x] Take 1 failure visible.  [x] Continuity Court verdict JSON visible. (real, `fail`/3)
- [x] Reshoot Spell generated.  [x] Only failed shot marked for reshoot. (S02 only)
- [x] Take Two Reveal visible. (before/after composite)
- [ ] ⚠️ Anchor Gate **approval** visible — fixture mode = approved; live run quarantined (gen didn't match markers). Use fixture take or regenerate for an approved demo.
- [x] Red-Thread Memory stores story + visual memory.
- [x] Auto Greenlight creates next cold open without user choice.

## Hard No-Go Before Submission (all currently FALSE = good)
- [x] (not true) Demo starts with CUT ritual, not tech explanation.
- [x] (not true) Qwen does verdict/repair/memory, not just prompt-gen.
- [x] (not true) Before/After is clear (composite).
- [x] (not true) Architecture shows Alibaba backend proof path.
- [x] (not true) Repo has MIT license.
- [ ] Demo length ≤3min — confirm when recorded.
- [x] (not true) Positioned as self-correcting loop, not a clay video generator.
