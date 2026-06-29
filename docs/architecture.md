# Circle Take Architecture

Accurate to the built system (GitHub renders the mermaid below). Also see `architecture.png`.

The AI runs on **Alibaba Cloud Model Studio (DashScope)** — Qwen (text + vision) and
Wan / HappyHorse (video) — and media is stored on **Alibaba Cloud OSS**. The single
deployment-proof file is `backend/app/alibaba_cloud_integration.py`.

## System

```mermaid
flowchart LR
  UI["UI /ui (watch public · BYOK key · capped judge-live)"] -->|"REST + X-Qwen-Key"| API

  subgraph API["FastAPI orchestrator (backend/app)"]
    EP["episode endpoints (anonymous)"]
    KR["key resolution: BYOK > judge-cap > fixture"]
    SM["state machine (state.py)"]
    DB[("ephemeral SQLite")]
    EP --> KR
    EP --> SM
    EP --> DB
  end

  API --> PIPE
  subgraph PIPE["pipeline (live, per request)"]
    SC["Scripty (agentic repair decision)"]
    RP["Reference Pack + route ladder (video_router)"]
  end

  PIPE --> QC["qwen_client.py"]
  PIPE --> VT["video_tasks.py (mode-aware)"]
  API --> OSS["oss_storage.py (oss2)"]

  QC -->|"chat + vision (qwen3.7-plus / qwen3-vl-plus)"| MS["Alibaba Cloud Model Studio (DashScope)"]
  VT -->|"t2v + reference-conditioned i2v/r2v/kf2v (Wan)"| MS
  OSS -->|"put_object / presign"| BUCKET[("Alibaba OSS: circle-take-media")]

  MS -. planning + vision verdicts .-> PIPE
```

## Golden-path state machine

```mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> CONTRACTED
  CONTRACTED --> STORYBOARDED
  STORYBOARDED --> GENERATING
  GENERATING --> TAKE_1_READY
  TAKE_1_READY --> REVIEWING
  REVIEWING --> CUT_REQUIRED
  CUT_REQUIRED --> RESHOOTING
  RESHOOTING --> TAKE_2_READY
  TAKE_2_READY --> ANCHOR_APPROVED: gate >= threshold
  TAKE_2_READY --> RESHOOTING: gate < threshold, ladder rungs remain (escalate)
  ANCHOR_APPROVED --> REMEMBERED
  REMEMBERED --> AUTO_GREENLIT
  AUTO_GREENLIT --> [*]
```

## Golden-path sequence (live)

The self-correction loop: the reshoot is **conditioned on a locked reference keyframe**
(Identity-Lock), Scripty **decides** the route, and the Anchor Gate drives
**approve / escalate / quarantine**. Verified live on the free tier: the
reference-conditioned reshoot scored **95/95/95 → approved** (vs. a blind-t2v 15/100
quarantine) — see `docs/evidence/reshoot-spike-2026-06-24.md`.

```mermaid
sequenceDiagram
  participant U as UI
  participant API as FastAPI
  participant MS as Alibaba Model Studio (Qwen + Wan)
  participant O as OSS
  U->>API: POST /api/episodes (brief)
  API->>MS: Qwen contracts + storyboard + Reference Pack
  API->>MS: Wan Take 1 (t2v, intentional drift)
  U->>API: POST /review
  API->>MS: Continuity Court (Qwen vision on Take 1 frame)
  MS-->>API: verdict = fail
  U->>API: POST /reshoot
  API->>MS: Scripty picks route -> reference-conditioned reshoot (i2v/r2v/kf2v)
  U->>API: POST /memory
  API->>MS: Anchor Gate (Qwen vision)
  alt gate >= threshold
    API-->>U: approved -> Red-Thread Memory + Auto Greenlight
  else gate < threshold, rungs remain
    API->>MS: escalate to next ladder route (reshoot again)
  else ladder exhausted
    API-->>U: honest quarantine (nothing greenlit)
  end
```
