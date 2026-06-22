# Cloud Run deploy (live Qwen+Wan + email auth + Neon Postgres)

The operational platform runs on Google Cloud Run: per-user email/JWT auth,
per-request live Qwen3.7 + Wan2.7 generation, and a persistent **Neon Postgres**
database so accounts and episodes survive Cloud Run's scale-to-zero cold starts.

## Prerequisites (one-time, user-provided)

1. **Neon Postgres** (free): create a project at <https://neon.tech>, copy the
   connection string, and put it in `circle-take/.env.local`:
   ```
   DATABASE_URL=postgresql://USER:PW@HOST/DB?sslmode=require
   ```
   (SQLite still works locally/tests; on Cloud Run it would be ephemeral.)
2. **JWT secret** in `.env.local` (or the deploy script generates one):
   ```
   JWT_SECRET=$(openssl rand -hex 32)
   ```
3. `QWEN_API_KEY`, `ALIBABA_CLOUD_*`, and the model IDs already live in `.env.local`.
4. `gcloud` authenticated (`gcloud auth login`) with a project set.

## Deploy

```bash
bash deployment/deploy_cloud_run.sh
```

The script builds an env-vars file from `.env.local` (forcing `APP_ENV=live`),
deploys from the `Dockerfile` (which installs **ffmpeg** for live frame
extraction), and prints the service URL + `/health` status. Secrets are passed as
Cloud Run service env vars and never committed.

## Verify (live)

```bash
B=https://<service-url>
# auth + isolation
curl -s -X POST $B/api/auth/register -H 'content-type: application/json' \
     -d '{"email":"you@x.com","password":"password123"}'        # -> {access_token}
curl -s -o /dev/null -w '%{http_code}\n' $B/api/episodes        # -> 401 (no token)
# full live run (Wan is async: poll between stages)
TOK=...; H="Authorization: Bearer $TOK"
EID=$(curl -s -X POST $B/api/episodes -H "$H" -d '{"title":"The Last Alarm"}' | jq -r .episode_id)
curl -s -X POST $B/api/episodes/$EID/generate -H "$H"           # Qwen text + start Wan Take 1
curl -s -X POST $B/api/episodes/$EID/take/1/poll -H "$H"        # repeat until take_1.status=succeeded
curl -s -X POST $B/api/episodes/$EID/review   -H "$H"           # real Qwen-vision verdict
curl -s -X POST $B/api/episodes/$EID/reshoot  -H "$H"           # spell + start Wan Take 2
curl -s -X POST $B/api/episodes/$EID/take/2/poll -H "$H"        # until take_2.status=succeeded
curl -s -X POST $B/api/episodes/$EID/memory   -H "$H"           # Anchor Gate + memory -> AUTO_GREENLIT
```

Cold-start persistence: after the service scales to zero, logging in again still
returns 200 and `GET /api/episodes` still lists your episodes (data is in Neon).
