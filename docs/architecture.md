# Circle Take Architecture

```text
Frontend Demo UI
  -> Alibaba Cloud Backend Orchestrator
  -> Qwen Cloud: planning, contracts, visual verdict, repair, memory
  -> Wan / HappyHorse: T2V, R2V, I2V, VideoEdit
  -> Object Storage: videos, frames, reference packs
  -> Database: episode state, contracts, verdicts, memory
  -> Production Report Export
```

Golden path state machine:

```text
DRAFT -> CONTRACTED -> STORYBOARDED -> GENERATING -> TAKE_1_READY -> REVIEWING -> CUT_REQUIRED -> RESHOOTING -> TAKE_2_READY -> ANCHOR_APPROVED -> REMEMBERED -> AUTO_GREENLIT
```
