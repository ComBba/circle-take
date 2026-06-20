# Official Sources Index

> **Rule (user mandate, 2026-06-20):** every implementation must be grounded in these
> first-party docs + best practices — never training memory. Before using any library
> API, confirm via its official doc below or via context7 MCP
> (`resolve-library-id` → `get-library-docs`). Re-verify "latest" at build time.

## Hackathon (authoritative)
- Rules: https://qwencloud-hackathon.devpost.com/rules
- Submission deadline: 2026-07-09 14:00 PT. Track 2 (AI Showrunner).

## Qwen Cloud / Alibaba Cloud Model Studio
- Models overview (model IDs, modalities): https://www.alibabacloud.com/help/en/model-studio/models
- Text-to-video (Wan) API reference: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
- Image-to-video (Wan) API reference: https://www.alibabacloud.com/help/en/model-studio/image-to-video-api-reference
- OpenAI-compatible chat endpoint: `POST https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions`
- Video synthesis endpoint: `POST https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`
  (header `X-DashScope-Async: enable`) → poll `GET .../api/v1/tasks/{task_id}`
- DashScope Python SDK: https://pypi.org/project/dashscope/

## Python libraries
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic v2: https://docs.pydantic.dev/latest/
- Uvicorn: https://www.uvicorn.org/
- httpx: https://www.python-httpx.org/
- Alibaba OSS SDK (oss2): https://www.alibabacloud.com/help/en/oss/developer-reference/python-sdk/
- pytest: https://docs.pytest.org/en/stable/

## Frontend
- Next.js 16: https://nextjs.org/docs

## Pinned versions (verified 2026-06-20 — re-verify on build day)
fastapi 0.138.0 · pydantic 2.13.4 · uvicorn 0.49.0 · httpx 0.28.1 ·
dashscope 1.25.23 · oss2 2.19.1 · pytest 9.1.1 · python-dotenv 1.2.2 · next 16.2.9
