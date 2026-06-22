#!/usr/bin/env bash
# Deploy Circle Take to Google Cloud Run with live Qwen+Wan + per-user auth.
#
# Secrets come from circle-take/.env.local (gitignored) and are passed to Cloud Run
# as service env vars via a temp env-vars-file (never committed, deleted on exit).
# Nothing secret is printed or stored in git.
#
# Required in .env.local for a full live + persistent deploy:
#   DATABASE_URL   postgresql://USER:PW@HOST/DB   (Neon; sqlite => ephemeral, warns)
#   JWT_SECRET     32+ bytes                       (auto-generated if absent)
#   QWEN_API_KEY, ALIBABA_CLOUD_* , QWEN_BASE_URL, QWEN_VIDEO_BASE_URL, WAN/QWEN models
#
# Usage:  bash deployment/deploy_cloud_run.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env.local"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-circle-take}"
ENV_YAML="$(mktemp -t ct_env.XXXXXX.yaml)"
trap 'rm -f "$ENV_YAML"' EXIT

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found"; exit 1; }

# Build the env-vars YAML from .env.local (APP_ENV forced live; JWT_SECRET ensured).
python3 - "$ENV_FILE" "$ENV_YAML" <<'PY'
import json, os, secrets, sys
from pathlib import Path
src, dst = sys.argv[1], sys.argv[2]
env = {}
for line in Path(src).read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    env[k.strip()] = v.strip().strip('"').strip("'")
keys = ["DATABASE_URL", "QWEN_API_KEY", "QWEN_BASE_URL", "QWEN_VIDEO_BASE_URL",
        "QWEN_TEXT_MODEL", "QWEN_VISION_MODEL", "WAN_T2V_MODEL", "WAN_I2V_MODEL",
        "WAN_R2V_MODEL", "WAN_VIDEOEDIT_MODEL", "ALIBABA_CLOUD_REGION",
        "ALIBABA_CLOUD_OSS_BUCKET", "ALIBABA_CLOUD_ACCESS_KEY_ID",
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET", "JWT_SECRET", "JWT_TTL_MINUTES"]
out = {"APP_ENV": "live"}  # force live regardless of local APP_ENV
for k in keys:
    if env.get(k):
        out[k] = env[k]
out.setdefault("JWT_SECRET", secrets.token_hex(32))  # ensure a strong secret
db = out.get("DATABASE_URL", "")
if not db.startswith(("postgres://", "postgresql://")):
    print("WARNING: DATABASE_URL is not Postgres -> data will NOT survive cold starts.", file=sys.stderr)
# json scalars are valid YAML -> safe quoting of URLs/secrets
Path(dst).write_text("\n".join(f"{k}: {json.dumps(v)}" for k, v in out.items()) + "\n")
print(f"env keys -> {sorted(out)}", file=sys.stderr)
PY

echo "Deploying $SERVICE to Cloud Run ($REGION)..."
gcloud run deploy "$SERVICE" \
  --source "$ROOT" \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 1Gi --cpu 1 --timeout 600 \
  --env-vars-file "$ENV_YAML" \
  --quiet

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo "Deployed: $URL"
echo "Health:  $(curl -s -o /dev/null -w '%{http_code}' "$URL/health")"
