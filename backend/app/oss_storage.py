"""Alibaba Cloud OSS storage — and the Devpost deployment proof.

This module uses the official `oss2` SDK to store Circle Take artifacts (videos,
keyframes, verdict JSON, production reports). It is the code file that
demonstrates Alibaba Cloud service/API usage required by the hackathon.

Runtime config (env): ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET,
ALIBABA_CLOUD_REGION (e.g. ap-southeast-1), ALIBABA_CLOUD_OSS_BUCKET.

Pure helpers (endpoint/object_url/load_config) have no network dependency and are
unit-tested; the put_* methods require live credentials + the bucket.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

_PLACEHOLDER = {"", "replace_me"}
_REQUIRED = (
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    "ALIBABA_CLOUD_REGION",
    "ALIBABA_CLOUD_OSS_BUCKET",
)


class OSSConfigError(RuntimeError):
    """Raised when OSS credentials/config are absent or still placeholders."""


@dataclass(frozen=True)
class OSSConfig:
    access_key_id: str
    access_key_secret: str
    region: str
    bucket: str


def endpoint(region: str) -> str:
    """International OSS endpoint for a region."""
    return f"https://oss-{region}.aliyuncs.com"


def object_url(bucket: str, region: str, key: str) -> str:
    """Public object URL (virtual-hosted style)."""
    return f"https://{bucket}.oss-{region}.aliyuncs.com/{key}"


def load_config() -> OSSConfig:
    vals = {k: os.getenv(k, "") for k in _REQUIRED}
    missing = [k for k, v in vals.items() if v in _PLACEHOLDER]
    if missing:
        raise OSSConfigError(
            "Missing Alibaba Cloud OSS config: " + ", ".join(missing)
        )
    return OSSConfig(
        access_key_id=vals["ALIBABA_CLOUD_ACCESS_KEY_ID"],
        access_key_secret=vals["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
        region=vals["ALIBABA_CLOUD_REGION"],
        bucket=vals["ALIBABA_CLOUD_OSS_BUCKET"],
    )


def _bucket(cfg: OSSConfig):
    import oss2  # lazy: module imports even where the SDK is unused

    auth = oss2.Auth(cfg.access_key_id, cfg.access_key_secret)
    return oss2.Bucket(auth, endpoint(cfg.region), cfg.bucket)


def put_bytes(key: str, data: bytes, content_type: Optional[str] = None) -> str:
    """Upload bytes; return the public object URL. Requires live credentials."""
    cfg = load_config()
    headers = {"Content-Type": content_type} if content_type else None
    _bucket(cfg).put_object(key, data, headers=headers)
    return object_url(cfg.bucket, cfg.region, key)


def put_file(key: str, path: str) -> str:
    """Upload a local file; return the public object URL. Requires live credentials."""
    cfg = load_config()
    _bucket(cfg).put_object_from_file(key, path)
    return object_url(cfg.bucket, cfg.region, key)
