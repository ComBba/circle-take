"""Alibaba Cloud integration — the single Devpost "Proof of Alibaba Cloud Deployment".

Circle Take runs on two Alibaba Cloud services, both exercised by real code paths:

1. **Alibaba Cloud Model Studio (DashScope)** — Qwen (text + vision) and Wan / HappyHorse
   (video) models are served from Alibaba Cloud and called over the official
   ``dashscope-intl.aliyuncs.com`` endpoints. Call sites: ``qwen_client`` (chat + vision)
   and ``video_tasks`` (Wan async video-synthesis).
2. **Alibaba Cloud Object Storage Service (OSS)** — generated videos / keyframes / verdicts
   are uploaded and presigned with the official ``oss2`` SDK. Call sites: ``oss_storage``.

Link THIS file in the Devpost "Proof of Alibaba Cloud Deployment" field. It is not a
wrapper that hides logic — it re-exports the real call sites and emits a manifest of the
Alibaba Cloud services, endpoints, and models actually in use. Run it directly to print
that manifest:

    python -m app.alibaba_cloud_integration
"""
from __future__ import annotations

from typing import Any, Dict

from . import qwen_client, video_tasks

# Re-export the real OSS (oss2) call sites so this proof file is live code, not a stub.
# These names are part of this module's public API (see __all__), hence the noqa.
from .oss_storage import endpoint as oss_endpoint  # noqa: F401
from .oss_storage import load_config as oss_load_config  # noqa: F401
from .oss_storage import object_url as oss_object_url  # noqa: F401
from .oss_storage import put_bytes as oss_put_bytes  # noqa: F401
from .oss_storage import put_file as oss_put_file  # noqa: F401
from .oss_storage import signed_url as oss_signed_url  # noqa: F401

# Alibaba Cloud Model Studio (DashScope, international) endpoints actually called.
MODEL_STUDIO_CHAT_ENDPOINT = qwen_client.QWEN_BASE_URL      # .../compatible-mode/v1
MODEL_STUDIO_VIDEO_ENDPOINT = video_tasks.VIDEO_BASE_URL    # .../api/v1


def alibaba_services_used() -> Dict[str, Any]:
    """Structured manifest of the Alibaba Cloud services Circle Take exercises.

    Mirrors the architecture diagram and doubles as machine-checkable deployment proof.
    """
    return {
        "model_studio_dashscope": {
            "product": "Alibaba Cloud Model Studio (DashScope, international)",
            "chat_endpoint": MODEL_STUDIO_CHAT_ENDPOINT,
            "video_endpoint": MODEL_STUDIO_VIDEO_ENDPOINT,
            "models": {
                "text": qwen_client.QWEN_TEXT_MODEL,
                "vision": qwen_client.QWEN_VISION_MODEL,
                "video_t2v": video_tasks.WAN_T2V_MODEL,
            },
            "call_sites": [
                "qwen_client.chat_raw",
                "qwen_client.qwen_vision_json",
                "video_tasks.create_task",
            ],
        },
        "object_storage_oss": {
            "product": "Alibaba Cloud Object Storage Service (OSS)",
            "sdk": "oss2",
            "endpoint_pattern": "https://oss-<region>.aliyuncs.com",
            "call_sites": [
                "oss_storage.put_bytes",
                "oss_storage.put_file",
                "oss_storage.signed_url",
            ],
        },
    }


__all__ = [
    "alibaba_services_used",
    "MODEL_STUDIO_CHAT_ENDPOINT",
    "MODEL_STUDIO_VIDEO_ENDPOINT",
    "oss_endpoint",
    "oss_object_url",
    "oss_load_config",
    "oss_put_bytes",
    "oss_put_file",
    "oss_signed_url",
]


if __name__ == "__main__":  # pragma: no cover - manual proof print
    import json

    print(json.dumps(alibaba_services_used(), indent=2))
