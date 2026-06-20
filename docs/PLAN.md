# Circle Take — 19-Day Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **위치 주의:** 이 파일은 아직 git repo가 없어 `claudedocs/`에 둡니다. **Phase 0에서 `circle-take` repo를 만든 직후 `docs/PLAN.md`로 이동**하세요.

**Goal:** Qwen Cloud(Track 2)에 제출할 Circle Take — 단일 golden path("The Last Alarm")를 실제 Qwen 추론 + Wan 비디오 생성 + Qwen 비전 판정 + Alibaba Cloud 배포로 end-to-end 실연하고, <3분 데모 영상과 함께 2026-07-09 마감 전 제출한다.

**Architecture:** FastAPI 오케스트레이터가 episode 상태기계(DRAFT→AUTO_GREENLIT)를 구동한다. 각 단계는 **먼저 golden-path fixture로 동작**(Phase 1)한 뒤 **실제 AI 호출로 교체**(Phase 2–3)하는 "fixture-first, then-real" 전략을 따른다. 차별화 핵심인 Continuity Court는 Qwen 비전 모델이 실제 생성 프레임을 읽고 verdict JSON을 반환한다. 산출물(영상·keyframe·verdict·memory)은 Alibaba Cloud OSS에 저장된다.

**Tech Stack (검증된 최신, 2026-06-20):** Python 3.12 · FastAPI 0.138.0 · Pydantic 2.13.4 · uvicorn 0.49.0 · httpx 0.28.1 · `dashscope` 1.25.23(or OpenAI-compatible) · `oss2` 2.19.1(Alibaba OSS SDK) · pytest 9.1.1 · SQLite · 최소 프론트(정적 HTML/JS 또는 **Next.js 16.2.9**) · Docker.

---

## Global Constraints

이 절은 **모든 task에 암묵 포함**된다. 값은 preflight에서 실측·확정한 것.

- **🔴 공식 문서 우선 + 최신 버전 강제 (사용자 필수 요건):** 모든 구현은 **추측 금지 — 공식 문서 + best practice에 근거**해야 한다. 라이브러리 통합 전 반드시 (a) 해당 공식 문서를 1차 출처로 확인(Alibaba Model Studio docs / 각 패키지 공식 문서), (b) **context7 MCP**(`resolve-library-id`→`get-library-docs`)로 최신 API 패턴 조회, (c) **버전은 implement 시점의 최신 stable로 재확인 후 핀**(아래 표는 2026-06-20 실측치 — 버전은 움직이므로 착수일에 `pip index`/registry로 재검증). 어떤 API/시그니처도 훈련 기억이 아니라 **문서·실측 응답으로 확정**한다.
- **제품 고정:** 이름 `Circle Take` / 태그라인 `Bad takes don't make the cut.` / Track 2 (AI Showrunner). `CUT`은 데모 시그니처 모먼트(제품명 아님). Clay Stop-Motion은 **MVP Style Contract**(제품 본질 아님). 사용자 branching 없음. Qwen = 판정자/감독/재촬영 지시자(프롬프트 생성기 아님).
- **단일 golden path:** `The Last Alarm` / actors `luna_cat`, `alarm_clock`, `worker` / `style_contract_id = clay_stop_motion_mvp` / 의도된 실패 = Luna 빨간 리본 소실 + 알람시계 종이 다이얼→디지털.
- **마감:** **2026-07-09 14:00 PT (= 07-10 06:00 KST)**. late 정책 없음. 데모 영상 **<3분, 첫 30초 = CUT ritual**, 호스팅은 **YouTube/Vimeo/Youku만**.
- **제출 필수물:** public OSS repo(**MIT**, 최상위 가시) · 영문 기능 설명 · **Alibaba Cloud 배포 proof(서비스/API 실사용 코드 파일)** · architecture diagram · 데모 영상 · Track 식별. 커밋은 **제출기간(05-26~) 내** 날짜.
- **정직성(DoD):** 최소 1개 verdict JSON은 **실제 visual/video 입력**에서 생성. 데모의 "의도된 실패"는 **진짜 탐지** 또는 **투명 공개** 중 하나 — 절대 조용한 staging 금지(자체 risk table 1순위).
- **검증된 API 사실(preflight):**
  - Host: `https://dashscope-intl.aliyuncs.com` (싱가포르/intl).
  - 비디오 생성(**최신 = Wan 2.7, 2026-04 출시, 2.6 대체**): `POST /api/v1/services/aigc/video-generation/video-synthesis` (헤더 `X-DashScope-Async: enable`) → `task_id` → `GET /api/v1/tasks/{task_id}` 폴링(1–5분). **Wan 2.7 4종이 PRD의 4 route와 1:1 대응**: `wan2.7-t2v`(T2V), `wan2.7-i2v`(I2V/first-frame), `wan2.7-r2v`(R2V/reference, character-critical), `wan2.7-videoedit`(VideoEdit/instruction edit=reshoot 1순위). I2V/R2V/edit은 input 스키마가 다름 — 각 공식 레퍼런스 확인.
  - 텍스트/비전(**최신 = Qwen3.7 시리즈**): OpenAI 호환 `POST /compatible-mode/v1/chat/completions`. **`qwen3.7-plus`는 실재·현행**(2026-06-01 GA, 저비용 *멀티모달*=vision/video understanding 내장 → **Continuity Court 비전 판정에 적합**). 무거운 추론은 `qwen3.7-max`(2026-05-19 GA, 1M ctx). 정확한 registry ID/모달리티는 **Phase 0에서 live 200 확인 후 핀**.
  - 인증: `Authorization: Bearer $QWEN_API_KEY` (DashScope API key).
- **비밀:** 실제 키는 `.env`에만. `.env`·`__pycache__/`·`.venv/`·생성 영상은 커밋 금지.

---

## Pinned Latest Versions (실측 2026-06-20 — 착수일 재검증 필수)

| 구성요소 | 최신 stable | 1차 출처 |
|---|---|---|
| fastapi | 0.138.0 | PyPI / fastapi.tiangolo.com |
| pydantic | 2.13.4 | PyPI / docs.pydantic.dev |
| uvicorn | 0.49.0 | PyPI |
| httpx | 0.28.1 | PyPI |
| dashscope | 1.25.23 | PyPI / Model Studio SDK docs |
| oss2 | 2.19.1 | PyPI / OSS SDK docs |
| pytest | 9.1.1 | PyPI |
| python-dotenv | 1.2.2 | PyPI |
| Next.js | 16.2.9 | npm / nextjs.org |
| Qwen 텍스트·비전 | `qwen3.7-plus` (GA 06-01) · `qwen3.7-max` (GA 05-19) | Model Studio `models` 문서 |
| Wan 비디오 | `wan2.7-t2v/i2v/r2v/videoedit` (04월) | Model Studio video API 레퍼런스 |

> `requirements.txt`는 **위 버전으로 핀**하되, 핀 직전 `pip index versions <pkg>`로 더 최신이 있으면 갱신. 라이브러리 API는 context7/공식 문서로 확인 후 사용.

## File Structure (목표 repo `circle-take/`)

`repo_starter/`를 시드로 확장한다. 책임 단위로 분리.

```text
circle-take/
  README.md  LICENSE  .gitignore  .env.example  Dockerfile  docker-compose.yml
  backend/
    requirements.txt
    app/
      main.py              # FastAPI 앱 + 7 엔드포인트 (얇게)
      schemas.py           # Pydantic v2 모델 (계약)
      state.py             # EpisodeState 상태기계 + 전이 규칙
      store.py             # SQLite 영속화 (episode/artifacts)
      contracts.py         # Qwen: Actor/Style/Story Contract 생성
      storyboard.py        # Qwen: storyboard slate + shot risk ledger
      route_selector.py    # T2V/R2V/I2V/VideoEdit 라우팅
      qwen_client.py       # Qwen 텍스트/비전 (OpenAI 호환) + JSON 강제/검증
      video_tasks.py       # Wan create→poll async 클라이언트
      continuity_court.py  # Qwen 비전 verdict (차별화 핵심)
      reshoot_spell.py     # delta 수리 지시 + fallback 체인
      anchor_gate.py       # 승인/격리 + 점수
      memory.py            # Red-Thread Memory + Auto Greenlight
      oss_storage.py       # Alibaba OSS 저장 (배포 proof 겸용)
  frontend/                # 8화면 최소 데모 UI
  examples/golden_path/    # 기존 9개 fixture (Phase 1 회귀 테스트 소스)
  deployment/
    alibaba_cloud_proof.md
    ecs_or_fc_deploy.md
  scripts/
    smoke_qwen.py          # Phase 0 live 검증
  tests/
    test_state.py test_store.py test_endpoints_fixture.py
    test_schemas.py test_qwen_json.py
  docs/
    PLAN.md  architecture.png  demo_script.md  devpost_submission.md
    validation_checklist.md  verified_models.md
```

---

## 일정 개요 (2026-06-20 → 07-09, ~19일)

| Phase | 기간(일차) | 산출 |
|---|---|---|
| 0 — Lock & Setup | D1 (06-20~21) | public repo, 검증된 키/모델, 데모-실패 전략 확정 |
| 1 — Orchestrator (fixture-first) | D2–4 | fixture로 전체 루프가 도는 API + green pytest |
| 2 — Qwen Integration | D4–7 | 실제 Qwen 계약/판정 산출물 (실 verdict ≥1) |
| 3 — Video Gen + Repair | D6–10 | 실제 Wan 영상 Take1/Take2 + before/after |
| 4 — Deploy + OSS + Frontend | D10–15 | 라이브 URL + 배포 proof + 8화면 UI |
| 5 — Demo + Devpost + Submit | D15–19 | <3분 영상, 제출 완료 (D18–19 버퍼) |

Phase 2·3은 의도적으로 겹친다(비디오 작업이 1–5분 비동기라 대기 중 Qwen 작업 진행).

---

# Phase 0 — Lock & Setup (D1)

**Phase Goal:** 코드 한 줄 짜기 전, **불확실성을 0으로** 만든다 — 공식문서·최신버전 핀·자격증명·실제 모델 ID·데모 실패 전략·repo 골격.

### Task 0.0: 공식 문서 북마크 + 최신 버전 핀 (사용자 필수 요건 운영화)

**Files:** Create `circle-take/docs/official_sources.md`, finalize `backend/requirements.txt`.

- [ ] **Step 1:** 착수일에 최신 stable 재검증(버전은 움직임)
```bash
for p in fastapi pydantic uvicorn httpx dashscope oss2 pytest python-dotenv; do
  echo -n "$p "; curl -s "https://pypi.org/pypi/$p/json" | python3 -c "import json,sys;print(json.load(sys.stdin)['info']['version'])"
done
curl -s https://registry.npmjs.org/next/latest | python3 -c "import json,sys;print('next',json.load(sys.stdin)['version'])"
```
- [ ] **Step 2:** `requirements.txt`를 재검증된 최신 버전으로 핀(`fastapi==0.138.0` 형식 — Step 1 출력 반영).
- [ ] **Step 3:** `official_sources.md`에 1차 출처 URL 고정: Model Studio `models`/video API 레퍼런스, FastAPI·Pydantic·dashscope·oss2 공식 문서. **구현 중 각 라이브러리는 context7(`resolve-library-id`→`get-library-docs`) 또는 이 문서의 공식 URL로 API 확인 후 사용**(훈련 기억 금지).
- [ ] **Step 4:** Commit `chore: pin latest deps + official source index`.

**DoD:** `requirements.txt`가 착수일 기준 최신 stable로 핀. `official_sources.md`에 모든 핵심 의존성의 공식 문서 URL.
**산출물:** 핀된 의존성 + 공식 출처 인덱스(이후 모든 구현 task의 근거).

### Task 0.1: Repo 초기화 + 공개

**Files:** Create `circle-take/.gitignore`, `circle-take/LICENSE`(MIT), move `repo_starter/*` → repo root.

- [ ] **Step 1:** 시드 복사 + git 초기화
```bash
cp -r circle_take_ready_pack/repo_starter circle-take && cd circle-take
git init -b main
```
- [ ] **Step 2:** `.gitignore` 작성
```gitignore
.env
.venv/
__pycache__/
*.pyc
backend/circle_take.db
artifacts/
*.mp4
*.png.tmp
.DS_Store
```
- [ ] **Step 3:** LICENSE 확인(MIT 이미 존재), 연도/저작자 확정. 첫 커밋
```bash
git add -A && git commit -m "chore: seed circle-take repo from readiness pack"
```
- [ ] **Step 4:** GitHub **public** repo 생성 + push (커밋 날짜 ≥ 05-26 확인)
```bash
gh repo create circle-take --public --source=. --remote=origin --push
gh repo view --json licenseInfo,visibility   # MIT + public 확인
```

**DoD:** `gh repo view`가 `"visibility":"PUBLIC"` + MIT license. 원격에 push됨.
**Risk:** 커밋 날짜가 제출기간 밖 → 신규성 요건 위반. (오늘 06-20이라 안전.)
**산출물:** 공개 repo URL (Devpost `[FILL]` 1개 해소).

### Task 0.2: Qwen Cloud 자격증명 + 실제 모델 ID live 확정

**Files:** Create `circle-take/scripts/smoke_qwen.py`, `circle-take/docs/verified_models.md`, `.env`(커밋 금지).

- [ ] **Step 1:** Qwen Cloud / Model Studio 계정·크레딧 발급, DashScope API key 발급. `.env`에 `QWEN_API_KEY=...` 저장. (사용자 직접 — `! ` 프리픽스로 로그인 명령 실행 가능.)
- [ ] **Step 2:** `scripts/smoke_qwen.py` 작성 — 텍스트·비전·비디오를 각 1회 실제 호출
```python
import os, time, httpx
KEY = os.environ["QWEN_API_KEY"]
H = {"Authorization": f"Bearer {KEY}"}
BASE = "https://dashscope-intl.aliyuncs.com"

def text(model):
    r = httpx.post(f"{BASE}/compatible-mode/v1/chat/completions", headers=H,
        json={"model": model, "messages":[{"role":"user","content":"reply OK"}]}, timeout=60)
    return r.status_code, r.text[:200]

def video(model):
    r = httpx.post(f"{BASE}/api/v1/services/aigc/video-generation/video-synthesis",
        headers={**H, "X-DashScope-Async":"enable", "Content-Type":"application/json"},
        json={"model": model, "input":{"prompt":"a clay cat waves, stop-motion"},
              "parameters":{"size":"1280*720"}}, timeout=60)
    return r.status_code, r.text[:300]

for m in ["qwen3.7-plus","qwen3.7-max"]:                  # 텍스트(최신) 후보
    print("TEXT", m, text(m))
for m in ["qwen3.7-plus"]:                                # 비전(qwen3.7-plus 멀티모달) 확인
    print("VL", m, text(m))
for m in ["wan2.7-t2v","wan2.7-i2v","wan2.7-r2v","wan2.7-videoedit"]:  # 비디오(최신 Wan2.7) 후보
    print("VIDEO", m, video(m))
```
- [ ] **Step 3:** 실행 후 **200 반환 모델만** `docs/verified_models.md`에 기록(텍스트/비전/비디오 각 1개 확정). 비디오는 반환된 `task_id`로 1회 폴링해 완료 영상 URL까지 확인.
```bash
python scripts/smoke_qwen.py | tee /tmp/smoke.txt
```
- [ ] **Step 4:** 확정 모델 ID를 `.env.example` 주석 + `verified_models.md`에 고정. 커밋(스모크 스크립트만, .env 제외).

**DoD:** `verified_models.md`에 **실제 200 응답으로 검증된** 텍스트/비전/비디오 모델 ID 3개 + 1개 비디오 task의 완료 영상 URL 기록.
**Risk:** 계정 승인 지연 / 모델 미지원 리전 → **D1에 반드시 해소**(이후 모든 Phase의 차단 의존성). 지연 시 즉시 사용자 에스컬레이션.
**산출물:** 검증된 모델 ID 문서, 동작하는 키.

### Task 0.3: 데모 "의도된 실패" 전략 확정 (리스크 #0)

**Files:** Create `circle-take/docs/demo_failure_strategy.md`.

- [ ] **Step 1:** 세 옵션 중 택1 결정 + 문서화:
  - (A) **진짜 생성→진짜 탐지:** Take 1을 리본 약화 프롬프트로 생성 → Court가 실제로 잡음. 가장 강하나 통제 어려움.
  - (B) **투명 공개 구성:** "리본 있는 버전"과 "리본 없는 버전"을 각각 생성해 Take1/Take2로 제시, **영상/README에 구성 방식 명시**. 정직·허용·통제 가능. → **권장 기본값.**
  - (C) 금지: 조용한 staging.
- [ ] **Step 2:** 선택안에 맞춘 프롬프트 2종(실패형/정상형)을 `examples/golden_path/`에 텍스트로 고정.

**DoD:** 전략 문서 + 프롬프트 2종 확정. 이후 Phase 3가 이 결정을 따른다.
**산출물:** `demo_failure_strategy.md`.

> **Gate 0 → 1:** Task 0.2 DoD(검증된 모델 ID)가 **반드시** 통과해야 Phase 2–3 진입 가능. 미통과 시 Phase 1(fixture-only)만 진행하며 병행 해소.

---

# Phase 1 — Orchestrator, fixture-first (D2–4)

**Phase Goal:** **AI 없이** golden-path fixture만으로 전체 상태기계가 7개 엔드포인트를 통해 DRAFT→AUTO_GREENLIT까지 도는 API. 이후 Phase가 모듈을 "실제 호출"로 교체해도 계약/테스트가 깨지지 않게 하는 토대.

### Task 1.1: 상태기계 + 스키마

**Files:** Modify `backend/app/schemas.py`; Create `backend/app/state.py`, `tests/test_state.py`, `tests/test_schemas.py`.

**Interfaces:**
- Produces: `EpisodeStatus` (Enum: DRAFT, CONTRACTED, STORYBOARDED, GENERATING, TAKE_1_READY, REVIEWING, CUT_REQUIRED, RESHOOTING, TAKE_2_READY, ANCHOR_APPROVED, REMEMBERED, AUTO_GREENLIT); `next_status(current: EpisodeStatus) -> EpisodeStatus`; `can_transition(a,b)->bool`.

- [ ] **Step 1: 실패 테스트 작성** `tests/test_state.py`
```python
from app.state import EpisodeStatus, next_status, can_transition
def test_linear_progression():
    assert next_status(EpisodeStatus.DRAFT) == EpisodeStatus.CONTRACTED
    assert next_status(EpisodeStatus.CUT_REQUIRED) == EpisodeStatus.RESHOOTING
def test_terminal_has_no_next():
    assert next_status(EpisodeStatus.AUTO_GREENLIT) is None
def test_illegal_transition_rejected():
    assert can_transition(EpisodeStatus.DRAFT, EpisodeStatus.REMEMBERED) is False
```
- [ ] **Step 2:** 실패 확인 `cd backend && python -m pytest tests/test_state.py -v` → ImportError 예상.
- [ ] **Step 3:** `state.py` 구현 — Enum + 순서 리스트 + `next_status`/`can_transition`(인접 전이만 허용).
- [ ] **Step 4:** 통과 확인 `python -m pytest tests/test_state.py -v` → PASS.
- [ ] **Step 5:** `schemas.py`에 `ContinuityVerdict`, `AnchorGateResult`(기존) + `StoryboardSlate`, `ShotRisk`, `RedThreadMemory`, `ProductionReport` 추가. `tests/test_schemas.py`로 fixture 9종을 모델에 로드해 검증.
```python
import json, glob
from app import schemas
def test_golden_fixtures_match_models():
    v = schemas.ContinuityVerdict(**json.load(open("../examples/golden_path/continuity_verdict_before.json")))
    assert v.verdict == "fail" and v.shot_id == "S02"
```
- [ ] **Step 6:** Commit `feat: episode state machine + pydantic contracts`.

**DoD:** `pytest tests/test_state.py tests/test_schemas.py` green. fixture 9종이 전부 모델에 로드됨.

### Task 1.2: SQLite 영속화

**Files:** Create `backend/app/store.py`, `tests/test_store.py`.

**Interfaces:** Produces `create_episode(brief)->str(id)`, `get_episode(id)->dict`, `update_status(id,status)`, `put_artifact(id,key,json)`, `get_artifact(id,key)`.

- [ ] **Step 1–4 (TDD):** `tests/test_store.py` — episode 생성→상태 갱신→artifact 저장/조회 왕복 테스트 작성→실패→`store.py`(sqlite3, JSON 컬럼) 구현→통과.
- [ ] **Step 5:** Commit `feat: sqlite episode + artifact store`.

**DoD:** 메모리/파일 SQLite에서 artifact 왕복 green.

### Task 1.3: 7개 엔드포인트 (fixture 구동)

**Files:** Modify `backend/app/main.py`; Create `tests/test_endpoints_fixture.py`.

**Interfaces:** `POST /api/episodes`, `GET /api/episodes/{id}`, `POST .../generate`, `POST .../review`, `POST .../reshoot`, `POST .../memory`, `GET .../report`. 이 단계에선 각 핸들러가 **해당 fixture를 로드해 artifact로 저장 + 상태 전이**.

- [ ] **Step 1:** `tests/test_endpoints_fixture.py` — FastAPI `TestClient`로 전체 시퀀스 호출, 마지막 `GET /report`가 `auto_greenlight.episode_2_title == "The Delivery Box"` 포함을 단언. (실패 작성)
- [ ] **Step 2:** 실패 확인.
- [ ] **Step 3:** `main.py` 구현 — 각 엔드포인트가 `examples/golden_path/*.json`을 로드→`put_artifact`→`update_status(next_status(...))`. `/review`는 `continuity_verdict_before.json`, `/reshoot`은 `reshoot_spell.txt`+`continuity_verdict_after.json`, `/memory`는 `red_thread_memory.json`.
- [ ] **Step 4:** 통과 확인 — 전체 루프 green.
- [ ] **Step 5:** 수동 스모크
```bash
uvicorn app.main:app --reload &
curl -s localhost:8000/health
curl -s -X POST localhost:8000/api/episodes -H 'content-type: application/json' -d @../examples/golden_path/brief.json
```
- [ ] **Step 6:** Commit `feat: golden-path orchestrator over fixtures (7 endpoints)`.

**DoD:** `TestClient`로 DRAFT→AUTO_GREENLIT 전체가 fixture만으로 green. `GET /report`가 production report JSON 반환.
**Risk:** 계약 표류 → schemas 단일 출처로 방지.
**산출물:** fixture로 도는 실행가능 API + 회귀 테스트.

> **이 시점에서 "데모 가능한 골격" 확보.** 이후 Phase는 모듈을 하나씩 실제 AI로 교체하되 `test_endpoints_fixture.py`(fixture 경로)를 회귀 가드로 유지.

---

# Phase 2 — Qwen Integration (D4–7)

**Phase Goal:** 계약·스토리보드·위험·라우팅·**Continuity Court**·reshoot·greenlight를 실제 Qwen 호출로 교체. **차별화 핵심 = 실제 비전 판정 1개 이상.**

### Task 2.1: 견고한 Qwen JSON 클라이언트

**Files:** Modify `backend/app/qwen_client.py`; Create `tests/test_qwen_json.py`.

**Interfaces:** Produces `async qwen_json(system:str, user:str|list, model:str, schema:type[BaseModel]) -> BaseModel` — chat 호출 + JSON 추출(fence-strip) + Pydantic 검증 + 1회 재시도. `qwen_vision_json(system, image_path_or_url, user, schema)`.

- [ ] **Step 1:** `tests/test_qwen_json.py` — monkeypatch로 가짜 응답(코드펜스 포함)을 주고 `qwen_json`이 깨끗한 모델 인스턴스를 반환하는지(실패→재시도 경로 포함) 단언. (네트워크 없이.)
- [ ] **Step 2–4 (TDD):** 실패→`qwen_client.py` 구현(OpenAI 호환 `chat/completions`, `verified_models.md`의 모델, `response_format={"type":"json_object"}` 시도 + 수동 fence-strip 폴백 + Pydantic 검증 + 1회 재시도)→통과.
- [ ] **Step 5:** Commit `feat: schema-validated Qwen JSON client with retry`.

**DoD:** 코드펜스/잡음 응답에도 스키마 검증된 객체 반환. 네트워크 없는 단위테스트 green.

### Task 2.2: 계약·스토리보드·위험 생성 (실 Qwen)

**Files:** Create `backend/app/contracts.py`, `backend/app/storyboard.py`; Modify `main.py`(`/episodes`, `/generate` 일부).

- [ ] **Step 1:** `contracts.py` — brief→Actor/Style/Story Contract를 `qwen_json`으로 생성(시스템 프롬프트는 PRD §9 규칙 반영, Luna `fixed_markers`/`forbidden_drift` 강제).
- [ ] **Step 2:** `storyboard.py` — 3–5 shot + Shot Risk Ledger 생성(S02 high-risk 보장 검증 규칙 포함).
- [ ] **Step 3:** `main.py`에서 fixture 로드 대신 이 모듈 호출로 교체(단, `APP_ENV=fixture`면 fixture 폴백 — 회귀 가드 유지).
- [ ] **Step 4:** live 통합 스모크 — 실제 brief로 호출, 생성된 계약 JSON을 `artifacts/`에 타임스탬프 저장.
```bash
APP_ENV=live python -m scripts.run_golden_path --stage contracts
```
- [ ] **Step 5:** Commit `feat: real Qwen contract + storyboard generation`.

**DoD:** 실제 Qwen이 brief로부터 Actor/Style/Story Contract + storyboard를 생성, 타임스탬프 artifact 저장. S02가 high-risk로 표시됨.
**Risk:** JSON 불안정 → 2.1의 검증/재시도로 흡수. 모델이 markers 누락 → 시스템 프롬프트에 명시 + 후처리 검증.

### Task 2.3: Continuity Court — 실제 비전 판정 (★차별화)

**Files:** Modify `backend/app/continuity_court.py`; Create `tests/test_continuity_contract.py`.

**Interfaces:** Produces `async judge(frame_path:str, actor_contracts, style_contract) -> ContinuityVerdict`.

- [ ] **Step 1:** 시스템 프롬프트 확정(기존 `CONTINUITY_COURT_SYSTEM` + "strict JSON, do not invent issues, compare against contracts").
- [ ] **Step 2:** `judge()` 구현 — 프레임 이미지 + 계약을 `qwen_vision_json`에 전달, `ContinuityVerdict` 반환.
- [ ] **Step 3:** **실제 비전 호출 검증** — "리본 없는 Luna 프레임"(Phase 0 전략의 실패형 또는 별도 준비 이미지)을 입력해 `verdict=="fail"` + `fixed_marker_missing(red ribbon)` 탐지 확인. 결과 JSON을 `artifacts/continuity_verdict_real.json`에 저장.
```bash
APP_ENV=live python -m scripts.run_golden_path --stage court --frame examples/golden_path/luna_no_ribbon.png
```
- [ ] **Step 4:** `test_continuity_contract.py` — 저장된 실제 verdict가 `ContinuityVerdict` 스키마에 부합하는지 회귀.
- [ ] **Step 5:** Commit `feat: real Qwen-vision Continuity Court (verdict from actual frame)`.

**DoD:** **실제 이미지 입력 → 실제 Qwen 비전 → 스키마 검증된 verdict JSON 1개** 산출·저장(정직성 DoD 충족). 리본 소실을 실제로 탐지.
**Risk:** 비전 모델이 위반을 못 잡음 → 프롬프트에 "fixed_markers를 명시적으로 대조" + 명확한 실패 프레임 사용. 그래도 실패 시 Phase 0(B) 투명 공개로 폴백하되 **판정 호출 자체는 실제 유지**.
**산출물:** `continuity_verdict_real.json` (데모·README의 "non-staged" 증거).

### Task 2.4: Reshoot Spell + Anchor Gate + Memory + Greenlight (실 Qwen)

**Files:** Modify `reshoot_spell.py`, `anchor_gate.py`(신규), `memory.py`.

- [ ] **Step 1:** `reshoot_spell.build(verdict, contracts)` — verdict의 violations만 반영한 delta 지시 + fallback route 명시(videoedit→r2v→rewrite).
- [ ] **Step 2:** `anchor_gate.evaluate(frame_path, contracts)` — Qwen 비전으로 identity/style/prop 점수 + approve/quarantine.
- [ ] **Step 3:** `memory.build(...)` + `auto_greenlight` — 승인 anchor만 저장, 다음 cold open 생성(실 Qwen).
- [ ] **Step 4:** 회귀(fixture 경로 green 유지) + live 스모크. Commit `feat: real reshoot/anchor-gate/memory/greenlight`.

**DoD:** reshoot 지시가 S02만 타겟. anchor gate 점수 실제 산출. memory가 승인분만 저장.

> **Gate 2:** 실제 verdict ≥1 산출(2.3 DoD) = 정직성 요건 충족. 이때부터 데모에 "실제 Qwen 판정" 제시 가능.

---

# Phase 3 — Video Generation + Repair (D6–10, Phase 2와 병행)

**Phase Goal:** 실제 Wan 영상으로 Take 1(특히 S02)과 Take Two를 생성, before/after 확보. 비동기(1–5분)라 Phase 2 작업과 겹쳐 진행.

### Task 3.1: Wan async 클라이언트 (create→poll)

**Files:** Modify `backend/app/video_tasks.py`; Create `tests/test_video_tasks.py`.

**Interfaces:** Produces `async create_t2v(prompt, model, size)->task_id`, `async poll(task_id, timeout=420)->video_url`, `async generate(prompt,...)->video_url`.

- [ ] **Step 1:** `test_video_tasks.py` — monkeypatch로 create(task_id 반환)·poll(상태 PENDING→SUCCEEDED+url) 시퀀스 단언(네트워크 없이).
- [ ] **Step 2–4 (TDD):** 실패→구현(검증된 엔드포인트 `/api/v1/services/aigc/video-generation/video-synthesis` + `X-DashScope-Async: enable`, 폴링 `/api/v1/tasks/{id}`, 지수백오프, 타임아웃)→통과.
- [ ] **Step 5:** **live 1샷 검증** — `verified_models.md` 비디오 모델로 실제 클립 1개 생성·다운로드.
```bash
APP_ENV=live python -m scripts.run_golden_path --stage video --shot S02
```
- [ ] **Step 6:** Commit `feat: Wan async video client (create->poll)`.

**DoD:** 실제 mp4 1개 생성·저장. 폴링 로직 단위테스트 green.
**Risk:** task 실패/타임아웃 → 재시도 + 명확한 에러 → fallback route 로깅(Technical 축 가점). 비용 → 생성 횟수 최소화(필요 shot만).

### Task 3.2: Take 1 생성 + 라우팅 + 의도된 실패

**Files:** Modify `route_selector.py`, `main.py`(`/generate`).

- [ ] **Step 1:** `route_selector.select(shot)` 실제화(risk/character_critical→r2v 등, 기존 로직 확장).
- [ ] **Step 2:** `/generate`가 storyboard의 각 shot을 라우팅→`video_tasks.generate` 호출, S02는 Phase 0 전략의 **실패형 프롬프트** 사용. 결과 URL/경로를 artifact 저장 + 상태 TAKE_1_READY.
- [ ] **Step 3:** live 스모크 — 최소 S02 Take 1 생성. (예산상 4 shot 전부는 선택; 데모는 S02 중심.)
- [ ] **Step 4:** Commit `feat: take-1 generation with route selection`.

**DoD:** S02 Take 1 실제 영상 + (가능하면) 나머지 shot. 라우팅 로그 존재.

### Task 3.3: Reshoot → Take Two → before/after

**Files:** Modify `main.py`(`/reshoot`), Create `scripts/make_before_after.py`.

- [ ] **Step 1:** `/reshoot`가 `reshoot_spell` + 정상형 프롬프트(또는 videoedit route)로 S02 Take Two 생성, 상태 TAKE_2_READY.
- [ ] **Step 2:** `anchor_gate`로 Take Two 평가→승인 시 ANCHOR_APPROVED→`/memory` 진행.
- [ ] **Step 3:** `make_before_after.py` — S02 Take1/Take2 키프레임을 좌우 비교 이미지로 합성(ffmpeg/PIL).
- [ ] **Step 4:** live 전체 골든패스 실행 — 실제 영상 기반 before/after 산출.
- [ ] **Step 5:** Commit `feat: reshoot take-two + before/after reveal`.

**DoD:** S02 before(리본 없음)/after(리본 복원) 실제 영상·이미지 확보. 나머지 shot 불변.
**Risk #0 실현:** Phase 0 전략대로(권장: 투명 공개). README/영상에 방식 명시.
**산출물:** 실제 Take1/Take2 mp4 + before/after 이미지.

---

# Phase 4 — Alibaba Cloud Deploy + OSS + Frontend (D10–15)

**Phase Goal:** 필수 산출물(배포 proof + 라이브 URL) 충족 + 데모/스크린샷이 성립하는 최소 UI.

### Task 4.1: OSS 저장 (배포 proof 겸용)

**Files:** Modify `backend/app/oss_storage.py`(기존 storage.py 대체); add `oss2` to requirements.

**Interfaces:** Produces `put_object(key, path|bytes)->url`, `list_episode_artifacts(id)->list`.

- [ ] **Step 1:** `oss2` SDK로 실제 OSS 버킷에 영상/keyframe/verdict 업로드 구현(자격증명은 env: `ALIBABA_CLOUD_*`).
- [ ] **Step 2:** live 검증 — 골든패스 산출물을 OSS에 업로드, 콘솔/`ossutil ls`로 객체 확인.
- [ ] **Step 3:** `deployment/alibaba_cloud_proof.md`에 **실제 버킷/리전/객체 URL + 이 코드 파일 링크** 기입.
- [ ] **Step 4:** Commit `feat: real Alibaba OSS storage (deployment proof)`.

**DoD:** OSS에 실제 객체 존재 + proof 파일이 Alibaba SDK 실사용 코드를 가리킴.

### Task 4.2: 백엔드 배포 (ECS 또는 Function Compute)

**Files:** Create `Dockerfile`, `docker-compose.yml`, `deployment/ecs_or_fc_deploy.md`.

- [ ] **Step 1:** `Dockerfile`(python:3.12-slim, uvicorn) + compose. 로컬 컨테이너 기동 확인.
- [ ] **Step 2:** Alibaba ECS(또는 Function Compute)에 배포, 공개 엔드포인트 확보. `/health` 200 확인.
```bash
curl -sI https://<live-host>/health -o /dev/null -w "%{http_code}\n"   # 200 기대
```
- [ ] **Step 3:** 배포 절차를 `ecs_or_fc_deploy.md`에 기록. Commit `chore: containerize + deploy to Alibaba Cloud`.

**DoD:** 라이브 URL이 HTTP 200(playbook A1 + 필수 testing link 충족).
**Risk:** 배포 디버깅 시간 → D10에 착수해 버퍼 확보. 비용 → 최소 인스턴스.

### Task 4.3: 최소 8화면 프론트엔드

**Files:** Create `frontend/`(정적 HTML+JS 또는 Next.js 단일 페이지).

- [ ] **Step 1:** 골든패스 8화면(Brief→Contracts→Slate→Take1→CUT/Court→Reshoot→Take Two Reveal→Memory) — 백엔드 호출 + artifact 표시.
- [ ] **Step 2:** **CUT 모먼트 화면**을 시그니처로 강조(영상의 첫 30초가 여기서 나옴).
- [ ] **Step 3:** 배포(정적이면 OSS+CDN 또는 동일 호스트). 라이브 데모 URL 확보.
- [ ] **Step 4:** 제품 스크린샷 ≥3장 캡처(첫화면/CUT/Take Two). Commit `feat: golden-path demo UI`.

**DoD:** 라이브 UI에서 골든패스가 보이고, CUT/Take Two/Memory가 화면에 표현됨. 스크린샷 3장 확보.
**산출물:** 라이브 데모 URL + 제품 스크린샷(축4 PARTIAL→PASS).

---

# Phase 5 — Demo + Devpost + Submit (D15–19)

**Phase Goal:** 제출. D18–19는 순수 버퍼.

### Task 5.1: <3분 데모 영상

- [ ] **Step 1:** `docs/demo_script.md`(기존 초단위 스크립트)대로 화면 녹화. **첫 30초 = CUT ritual**(Take1 실패→CUT→실제 verdict JSON).
- [ ] **Step 2:** 실제 산출물(verdict JSON, before/after, 라이브 UI) 위주로 편집, 길이 <3:00 확인.
- [ ] **Step 3:** **YouTube/Vimeo/Youku 중 하나에 public 업로드.** (Loom/Facebook 불가.)

**DoD:** 공개 영상 <3분, 첫 30초 CUT, 실제 동작 표시. (POST-DEV 항목.)

### Task 5.2: Devpost 작성 + 제출

**Files:** Modify `docs/devpost_submission.md`(`[FILL]` 해소).

- [ ] **Step 1:** repo URL · 데모 영상 URL · 라이브 testing URL · Alibaba 배포 proof 링크 · architecture diagram 링크 · 프론트 스택 · 라이선스(MIT) 채움.
- [ ] **Step 2:** README 보강 — badges(license/live demo), 라이브 URL 표, Qwen 사용 matrix, 스크린샷, 골든패스 실행법.
- [ ] **Step 3:** `docs/validation_checklist.md` 전 항목 점검(특히 "Hard No-Go" 7개 모두 해당 없음 확인).
- [ ] **Step 4:** Devpost 폼 제출, **Track 2 단일 선택**. (선택)보너스용 블로그/소셜 포스트.

**DoD:** validation checklist 전부 green, Hard-No-Go 0건, Devpost 제출 완료.
**Risk:** 마감 직전 혼잡 → **D17까지 제출 목표**, D18–19 버퍼.

### Task 5.3: 최종 자기검증

- [ ] **Step 1:** 라이브 URL HTTP 200 재확인, 영상 public 재생 확인, repo public+MIT 재확인.
- [ ] **Step 2:** "first 30s = CUT" / "Qwen이 prompt-gen만으로 보이지 않음" / "before-after 명확" 등 No-Go 항목 최종 점검.
- [ ] **Step 3:** 제출 스냅샷 태그 `git tag submission-v1 && git push --tags`.

**DoD:** 모든 제출 필수물 라이브 검증 통과.

---

## Self-Review (spec 대비 커버리지)

- **필수 산출물 5종** → repo(0.1)·기능설명(5.2)·**Alibaba proof(4.1)**·architecture(기존+5.2)·영상(5.1)·Track(5.2) ✅
- **Track 2 4요소**(script/storyboard/generation/editing) → contracts·storyboard(2.2)·video(3.2)·reshoot/videoedit(3.3) ✅
- **차별화(self-correction)** → Court(2.3)·Reshoot(2.4)·Anchor Gate(2.4)·Memory(2.4) ✅
- **정직성 DoD(실 verdict ≥1)** → 2.3 ✅ / **데모 실패 전략** → 0.3 ✅
- **심사 가중치 대응:** Innovation/Technical(60%) = Phase 2–3에 시간 집중 ✅ / Presentation(15%) = Phase 5 ✅
- **검증 체크리스트 Hard-No-Go 7종** → 5.2 Step3에서 일괄 점검 ✅
- **미커버 위험:** 비디오 생성 비용·시간 변동성 → S02 중심 최소 생성으로 완화(3.2 주). 모델 ID 불확실 → 0.2에서 live 확정(차단 의존성).

---

## 실행 방식 선택

계획서는 `claudedocs/circle-take-19day-implementation-plan.md`에 저장되었습니다. 두 가지 실행 옵션:

1. **Subagent-Driven (권장)** — task마다 fresh subagent dispatch + task 사이 리뷰. 빠른 반복, 컨텍스트 격리.
2. **Inline Execution** — 이 세션에서 `executing-plans`로 체크포인트 단위 배치 실행.

어느 방식으로 진행할까요? (또는 계획서만 받고 직접 실행하셔도 됩니다.)
