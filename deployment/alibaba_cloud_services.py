"""Alibaba Cloud deployment proof — real `oss2` SDK usage.

This is the code file Devpost asks for: proof of Alibaba Cloud service/API use.
The canonical, unit-tested storage integration lives in
``backend/app/oss_storage.py``; this entrypoint demonstrates the same OSS API
surface standalone and is safe to link as the deployment proof.

Runtime env: ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET,
ALIBABA_CLOUD_REGION (e.g. ap-southeast-1), ALIBABA_CLOUD_OSS_BUCKET.
"""
from __future__ import annotations

import os

import oss2  # official Alibaba Cloud OSS SDK (pinned in backend/requirements.txt)

ALIBABA_CLOUD_REGION = os.getenv("ALIBABA_CLOUD_REGION", "ap-southeast-1")
ALIBABA_CLOUD_OSS_BUCKET = os.getenv("ALIBABA_CLOUD_OSS_BUCKET", "")


def oss_endpoint() -> str:
    return f"https://oss-{ALIBABA_CLOUD_REGION}.aliyuncs.com"


def make_bucket() -> "oss2.Bucket":
    """Build an authenticated OSS bucket client (requires live credentials)."""
    auth = oss2.Auth(
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
    )
    return oss2.Bucket(auth, oss_endpoint(), ALIBABA_CLOUD_OSS_BUCKET)


def upload_artifact(key: str, local_path: str) -> str:
    """Upload a generated artifact to OSS and return its public URL."""
    make_bucket().put_object_from_file(key, local_path)
    return f"https://{ALIBABA_CLOUD_OSS_BUCKET}.oss-{ALIBABA_CLOUD_REGION}.aliyuncs.com/{key}"


def deployment_proof_summary() -> dict:
    return {
        "sdk": "oss2",
        "service": "Alibaba Cloud OSS",
        "region": ALIBABA_CLOUD_REGION,
        "bucket": ALIBABA_CLOUD_OSS_BUCKET,
        "purpose": "Store Circle Take videos, keyframes, verdict JSON, production reports.",
        "canonical_module": "backend/app/oss_storage.py",
    }
