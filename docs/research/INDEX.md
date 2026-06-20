# Research / Knowledge Index

Queryable index of saved references and findings (per "document everything"). Search here first.

| Doc | What's in it |
|---|---|
| [qwen-cloud-integration.md](qwen-cloud-integration.md) | Endpoints, live-confirmed models, `json_object` gotcha, structured-output strategy, vision input, OSS |
| [hackathon-alignment.md](hackathon-alignment.md) | Hackathon rules/resources + how Circle Take meets each deliverable + judging weights |
| [lessons-learned.md](lessons-learned.md) | Self-correction log (symptom→cause→fix) + standing rules |
| ../official_sources.md | First-party doc URLs + pinned versions |
| ../verified_models.md | Live-confirmed model IDs + smoke results |
| ../evidence/ | Real Qwen/Wan output artifacts (proof, committed) |

**Key facts (fast recall):**
- Hackathon: *Global AI Hackathon Series with Qwen Cloud* · Track 2 (AI Showrunner) · deadline **2026-07-09 14:00 PDT**.
- API base: `dashscope-intl.aliyuncs.com/compatible-mode/v1` (OpenAI-compatible). Models: `qwen3.7-plus` (text+vision), `wan2.7-t2v` (video). OSS bucket `circle-take-media` (ap-southeast-1).
- Secrets in `.env.local`. Git remote: `ComBba/circle-take` (personal, public). Deploy: local Docker (free).
