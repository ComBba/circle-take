# Circle Take Architecture

Accurate to the built system (GitHub renders the mermaid below). Also see `architecture.png`.

## System

```mermaid
flowchart LR
  UI["Demo UI /ui (vanilla JS)"] -->|REST| API

  subgraph API["FastAPI orchestrator (backend/app)"]
    EP["7 endpoints (main.py)"]
    SM["state machine (state.py)"]
    DB[("SQLite (store.py)")]
    CFG["fixture / live (config.py)"]
    EP --> SM
    EP --> DB
    EP --> CFG
  end

  API --> QC["qwen_client.py"]
  API --> VT["video_tasks.py"]
  API --> OSS["oss_storage.py (oss2)"]

  QC -->|"chat + vision (qwen3.7-plus)"| QWEN["Qwen Cloud (compatible-mode/v1)"]
  VT -->|"create to poll (wan2.7-t2v)"| WAN["Wan 2.7 (video-synthesis)"]
  OSS -->|"put_object"| BUCKET[("Alibaba OSS: circle-take-media")]

  QWEN -. planning .-> EP
  QWEN -. vision verdicts .-> EP
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
  TAKE_2_READY --> ANCHOR_APPROVED
  ANCHOR_APPROVED --> REMEMBERED
  REMEMBERED --> AUTO_GREENLIT
  AUTO_GREENLIT --> [*]
```

## Golden-path sequence (live)

```mermaid
sequenceDiagram
  participant U as Demo UI
  participant API as FastAPI
  participant Q as Qwen3.7
  participant W as Wan2.7
  participant O as OSS
  U->>API: POST /api/episodes (brief)
  API->>Q: contracts + storyboard
  API->>W: generate Take 1 (create to poll)
  W-->>API: mp4 then ffmpeg frame
  API->>O: store clip + frame
  U->>API: POST /review
  API->>Q: Continuity Court (vision on frame)
  Q-->>API: verdict = fail
  U->>API: POST /reshoot
  API->>W: Take Two (videoedit / r2v)
  U->>API: POST /memory
  API->>Q: Anchor Gate (vision)
  API-->>U: Red-Thread Memory + Auto Greenlight
```
