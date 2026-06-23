# Cloud Run deploy (BYOK, no storage)

Circle Take runs on Google Cloud Run with **no server-side Qwen key and no accounts**:
- **Watch the loop** is public (golden-path fixtures + presigned demo clips), no key.
- **Run your own** live episode is **BYOK** — the browser sends the caller's Qwen key
  via the `X-Qwen-Key` header, used per request and never stored or logged.
- Episode state is ephemeral SQLite (`/tmp`); a single instance keeps it consistent.

## What the service needs (env)

Non-secret config + the OSS creds that presign the public demo clips — **not** a Qwen
key, **not** a JWT secret:

```
APP_ENV=live
DATABASE_URL=sqlite:////tmp/circle_take.db
QWEN_BASE_URL, QWEN_VIDEO_BASE_URL, QWEN_TEXT_MODEL, QWEN_VISION_MODEL, WAN_*_MODEL
ALIBABA_CLOUD_REGION, ALIBABA_CLOUD_OSS_BUCKET, ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET
```

## Deploy

```bash
# Build the env-vars file from .env.local (omits QWEN_API_KEY + JWT):
# (see the inline builder in this repo's deploy history, or hand-write the keys above)
gcloud run deploy circle-take \
  --project <PROJECT> --source . --region us-central1 \
  --allow-unauthenticated --memory 1Gi --cpu 1 --timeout 600 \
  --max-instances 1 --clear-cloudsql-instances \
  --env-vars-file env.yaml --quiet
```

`--max-instances 1` keeps the ephemeral SQLite state consistent across a multi-step run;
`--clear-cloudsql-instances` removes any prior database attachment (BYOK stores nothing).

## Verify (live)

```bash
B=https://<service-url>
curl -s $B/health                                   # mode: live
curl -s -o /dev/null -w '%{http_code}\n' $B/api/demo            # 200 (public, no key)
curl -s -o /dev/null -w '%{http_code}\n' -X POST $B/api/auth/register  # 404 (no accounts)
# BYOK live run:
H='X-Qwen-Key: sk-...'
EID=$(curl -s -X POST $B/api/episodes -d '{"title":"x"}' -H 'content-type: application/json' | jq -r .episode_id)
curl -s -X POST $B/api/episodes/$EID/generate -H "$H"      # live Qwen + Wan
curl -s -X POST $B/api/episodes/$EID/take/1/poll -H "$H"   # repeat until take_1.status=succeeded
# take_1.video_url is the caller's own DashScope URL (nothing stored on our side)
```

Without `X-Qwen-Key`, the same endpoints replay golden-path fixtures (no Qwen calls).
