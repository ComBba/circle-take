# Qwen Cloud Integration — verified notes

> Knowledge base for Circle Take's Qwen Cloud / Alibaba Cloud integration. Every entry is
> grounded in official docs or an empirical live result (dated 2026-06-21). Update as we learn.

## Endpoints (live-verified)
- **Chat (text + vision), OpenAI-compatible:** `https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions`
- **Video synthesis (async):** `POST https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`
  with header `X-DashScope-Async: enable` → returns `task_id` → poll `GET .../api/v1/tasks/{task_id}` (1–5 min).
- **Auth:** `Authorization: Bearer $QWEN_API_KEY`.
- Official resources confirm OpenAI compatibility: *"The API is OpenAI-compatible, so you can use the OpenAI SDK in Python or Node.js."* We use `httpx` directly (same wire format, one fewer dep); the OpenAI SDK is an equally valid official path.

## Models (live-confirmed HTTP 200 / real output, 2026-06-21)
| Role | Model | Evidence |
|---|---|---|
| Text / contracts / storyboard | `qwen3.7-plus` | 200, real JSON contracts generated |
| Heavy reasoning (optional) | `qwen3.7-max` | 200 |
| Vision (Continuity Court / Anchor Gate) | `qwen3.7-plus` (multimodal) | real verdict on a real frame (see docs/evidence) |
| Text-to-video | `wan2.7-t2v` | real task created→polled→SUCCEEDED→mp4 |
| I2V / R2V / videoedit | `wan2.7-i2v` / `wan2.7-r2v` / `wan2.7-videoedit` | doc-verified (Wan 2.7 suite); t2v live-proven |

## ⚠️ Gotcha: `response_format=json_object` requires the word "json" in the prompt
Empirically proven (2026-06-21). Calling chat/completions with
`response_format={"type":"json_object"}` but **no literal "json" in any message** returns:

```
HTTP 400 InvalidParameter: 'messages' must contain the word 'json' in some form,
to use 'response_format' of type 'json_object'.
```

Adding "json" to the prompt → 200. **Fix:** `qwen_client._json_loop` appends a system
message ("Respond with a single valid JSON object.") whenever no "json" token is present.
Best practice: always (a) set `response_format=json_object` AND (b) mention JSON in the prompt.

## Structured output strategy (best practice)
1. `response_format={"type":"json_object"}` to force a JSON body.
2. Prompt explicitly names the JSON shape (and contains the word "json").
3. Client strips ``` fences + extracts the outer `{...}` (`_extract_json`).
4. Validate against a Pydantic v2 schema; on failure, **reprompt once** with the validation error.
   (`qwen_client.qwen_json` / `qwen_vision_json`.)

## Vision input (Continuity Court / Anchor Gate)
OpenAI-compatible multimodal message: user content is a list of
`{"type":"text",...}` + `{"type":"image_url","image_url":{"url": <http|data-uri>}}`.
Local frames are sent as base64 `data:` URIs (`_image_content`).

## Alibaba Cloud OSS (storage + deployment proof)
- SDK `oss2` (pinned 2.19.1). `oss2.Auth(id, secret)` + `oss2.Bucket(auth, endpoint, bucket)`.
- Endpoint: `https://oss-<region>.aliyuncs.com` (e.g. `ap-southeast-1`).
- Object URL: `https://<bucket>.oss-<region>.aliyuncs.com/<key>`.
- Bucket `circle-take-media` (ap-southeast-1, private ACL). Read via `sign_url("GET", key, ttl)`.
- `UserDisable` error = OSS service not activated on the account (one-time console activation).
- `AccessDenied oss:*` = RAM user lacks `AliyunOSSFullAccess`.

## Official sources
- Resources hub: https://qwencloud-hackathon.devpost.com/resources
- Model Studio docs: https://www.alibabacloud.com/help/en/model-studio/
- Text-to-video API: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
- OSS Python SDK: https://www.alibabacloud.com/help/en/oss/developer-reference/python-sdk/
