# Deploy Circle Take on Alibaba Cloud

Two supported paths. **A (ECS + Docker Compose)** is the simplest and matches the repo's
`Dockerfile` + `docker-compose.yml`. **B (Function Compute)** is serverless. Both produce
the public **Backend URL** and exercise Alibaba Cloud (compute + OSS) — the deployment proof.

Prereqs: an Alibaba Cloud account, a RAM user with OSS access, and the four env vars in
`.env` (`QWEN_API_KEY`, `ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET`, `ALIBABA_CLOUD_REGION`,
`ALIBABA_CLOUD_OSS_BUCKET`). **Never commit `.env`** (it is gitignored).

## 0. Create an OSS bucket (storage + proof)

```bash
# Console → Object Storage Service → Create Bucket (same region as compute), or ossutil:
ossutil mb oss://<your-bucket> --region <region>      # e.g. ap-southeast-1
```

## A. ECS + Docker Compose (recommended)

1. **Create an ECS instance** (Ubuntu 22.04+, smallest burstable is fine). Open security
   group inbound **80/443** (and 8000 if testing directly).
2. **Install Docker** on the instance:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER && newgrp docker
   ```
3. **Ship the repo** (git clone the public repo, or `scp` it) to the instance.
4. **Create `.env`** on the instance (not in git) with the four required vars + `APP_ENV=live`.
5. **Run**:
   ```bash
   docker compose up -d --build
   curl -sI http://localhost:8000/health      # expect 200
   ```
6. **HTTPS + public URL**: put the service behind a reverse proxy (Nginx/Caddy) or an
   Alibaba **SLB/ALB** with an HTTPS listener → your public **Backend URL**.

Record the Backend URL in `alibaba_cloud_proof.md` and the Devpost form.

## B. Function Compute (serverless container)

1. Build & push the image to **Alibaba Cloud Container Registry (ACR)**:
   ```bash
   docker build -t registry.<region>.aliyuncs.com/<ns>/circle-take:latest .
   docker push registry.<region>.aliyuncs.com/<ns>/circle-take:latest
   ```
2. Create a **Function Compute** custom-container function from that image; set the
   listening port to **8000** and add the env vars.
3. Enable an **HTTP trigger** → that URL is your public **Backend URL**.

## Verify the demo end-to-end

```bash
BASE=https://<backend-url>
curl -s $BASE/health
EID=$(curl -s -X POST $BASE/api/episodes -H 'content-type: application/json' -d '{"title":"The Last Alarm"}' | python -c "import sys,json;print(json.load(sys.stdin)['episode_id'])")
for s in generate review reshoot memory; do curl -s -X POST $BASE/api/episodes/$EID/$s >/dev/null; done
curl -s $BASE/api/episodes/$EID/report
open  "$BASE/ui/"      # the browser demo
```

## Cost note

Use the smallest instance/function tier; the hackathon provides free Qwen Cloud credits.
Stop/scale down compute when not demoing. Generated media lives in OSS (cheap), not in the
container.
