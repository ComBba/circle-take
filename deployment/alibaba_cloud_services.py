"""Deployment proof placeholder.

Replace with actual Alibaba Cloud SDK/API usage before submission.
This file exists so the repo has a clear place for the required deployment proof.
"""

import os

ALIBABA_CLOUD_REGION = os.getenv("ALIBABA_CLOUD_REGION")
ALIBABA_CLOUD_OSS_BUCKET = os.getenv("ALIBABA_CLOUD_OSS_BUCKET")

def deployment_proof_summary():
    return {
        "region": ALIBABA_CLOUD_REGION,
        "oss_bucket": ALIBABA_CLOUD_OSS_BUCKET,
        "purpose": "Store Circle Take generated videos, keyframes, verdict JSON, and production reports."
    }
