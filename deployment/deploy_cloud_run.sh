#!/usr/bin/env bash
# Deploy Circle Take to Google Cloud Run in BYOK mode (no server Qwen key, no accounts).
#
# The service env carries ONLY non-secret config + the OSS creds that presign the public
# demo clips — never a Qwen key (live runs are BYOK via the X-Qwen-Key header) and never a
# JWT secret (no accounts). Episode state is ephemeral SQLite on a single instance.
#
# Usage:  bash deployment/deploy_cloud_run.sh [PROJECT_ID]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env.local"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-circle-take}"
PROJECT="${1:-$(gcloud config get-value project 2>/dev/null)}"
ENV_YAML="$(mktemp -t ct_byok.XXXXXX.yaml)"
trap 'rm -f "$ENV_YAML"' EXIT

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found"; exit 1; }

python3 - "$ENV_FILE" "$ENV_YAML" <<'PY'
import json, sys
from pathlib import Path
src, dst = sys.argv[1], sys.argv[2]
env = {}
for line in Path(src).read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
out = {"APP_ENV": "live", "DATABASE_URL": "sqlite:////tmp/circle_take.db"}
for k in ["QWEN_BASE_URL", "QWEN_VIDEO_BASE_URL", "QWEN_TEXT_MODEL", "QWEN_VISION_MODEL",
          "WAN_T2V_MODEL", "WAN_I2V_MODEL", "WAN_R2V_MODEL", "WAN_VIDEOEDIT_MODEL",
          "ALIBABA_CLOUD_REGION", "ALIBABA_CLOUD_OSS_BUCKET",
          "ALIBABA_CLOUD_ACCESS_KEY_ID", "ALIBABA_CLOUD_ACCESS_KEY_SECRET"]:
    if env.get(k):
        out[k] = env[k]
# Deliberately omitted: QWEN_API_KEY (BYOK) and JWT_SECRET (no accounts).
Path(dst).write_text("\n".join(f"{k}: {json.dumps(v)}" for k, v in out.items()) + "\n")
print(f"BYOK env keys: {len(out)} (QWEN_API_KEY present: {'QWEN_API_KEY' in out})", file=sys.stderr)
PY

echo "Deploying $SERVICE (BYOK) to $PROJECT / $REGION ..."
gcloud run deploy "$SERVICE" \
  --project "$PROJECT" --source "$ROOT" --region "$REGION" \
  --allow-unauthenticated --memory 1Gi --cpu 1 --timeout 600 \
  --max-instances 1 --clear-cloudsql-instances \
  --env-vars-file "$ENV_YAML" --quiet

URL="$(gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" --format='value(status.url)')"
echo "Deployed: $URL"
echo "Health:   $(curl -s -o /dev/null -w '%{http_code}' "$URL/health")"
