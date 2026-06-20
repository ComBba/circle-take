# Circle Take - 검증 및 제출 체크리스트

## Stage One Pass/Fail

- [ ] Track 2로 명확히 식별했다.
- [ ] Qwen Cloud API 사용이 코드와 데모에서 보인다.
- [ ] Wan / HappyHorse video generation 또는 editing 계열 사용이 보인다.
- [ ] Scriptwriting, storyboarding, generation, editing이 모두 들어간다.
- [ ] 프로젝트가 영상/텍스트 설명과 동일하게 작동한다.

## Stage Two Scoring Defense

### Innovation & AI Creativity 30%

- [ ] Circle Take가 단순 video generator가 아니라 self-correcting production loop로 설명된다.
- [ ] Continuity Court, Reshoot Spell, Anchor Gate, Red-Thread Memory가 보인다.
- [ ] Qwen이 planning, route selection, verdict, repair, memory gate에서 쓰인다.
- [ ] CUT ritual이 첫 30초 안에 나온다.

### Technical Depth & Engineering 30%

- [ ] Architecture diagram에 frontend, Alibaba Cloud backend, Qwen Cloud, storage/database가 보인다.
- [ ] Repo에 backend orchestrator 코드가 있다.
- [ ] Async video task polling 또는 task state management가 있다.
- [ ] Error fallback이 있다: VideoEdit -> R2V regeneration -> shot rewrite.
- [ ] JSON schemas와 golden path artifacts가 repo에 있다.

### Problem Value & Impact 25%

- [ ] "one clip generation"이 아니라 "repeatable character episode production" 문제로 설명한다.
- [ ] Short-form creators / character IP makers가 primary users로 명시된다.
- [ ] Approved visual anchors와 story memory가 다음 episode에 이어진다는 점이 보인다.

### Presentation & Documentation 15%

- [ ] Demo is under 3 minutes.
- [ ] First 30 seconds show the key logic visually.
- [ ] README has setup instructions.
- [ ] Devpost form is in English.
- [ ] Architecture docs are clear.

## Official Submission Requirements

- [ ] Public code repository URL.
- [ ] Open-source license visible at top level.
- [ ] Text description explaining features/functionality.
- [ ] Proof of Alibaba Cloud Deployment: link to code file showing Alibaba Cloud services/APIs.
- [ ] Architecture diagram showing Qwen Cloud, backend, database/storage, frontend.
- [ ] Demo video under 3 minutes and publicly visible on YouTube/Vimeo/Youku.
- [ ] Demo video shows project functioning.
- [ ] No unauthorized third-party trademarks, copyrighted music, or copyrighted materials.
- [ ] Track identified as Track 2.
- [ ] Testing link or build available free until judging ends.
- [ ] English translation/materials available.

## Golden Path Verification

- [ ] User brief loads.
- [ ] Actor Contract generated.
- [ ] Style Contract generated.
- [ ] Storyboard Slate generated.
- [ ] Shot Risk Ledger generated.
- [ ] Take 1 failure visible.
- [ ] Continuity Court verdict JSON visible.
- [ ] Reshoot Spell generated.
- [ ] Only failed shot marked for reshoot.
- [ ] Take Two Reveal visible.
- [ ] Anchor Gate approval visible.
- [ ] Red-Thread Memory stores story + visual memory.
- [ ] Auto Greenlight creates next cold open without user choice.

## Hard No-Go Before Submission

Do not submit if any of the following is true.

- [ ] Demo starts with technical explanation instead of CUT ritual.
- [ ] Qwen's role looks like prompt generation only.
- [ ] Before/After repair is unclear.
- [ ] Architecture diagram does not show Alibaba Cloud backend proof path.
- [ ] Repo has no license.
- [ ] Demo is longer than 3 minutes.
- [ ] Project is described as a clay video generator.
