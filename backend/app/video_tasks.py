"""Wan video generation client (DashScope intl, async create -> poll).

Verified API: POST .../services/aigc/video-generation/video-synthesis with header
X-DashScope-Async: enable returns a task_id; GET .../tasks/{id} until SUCCEEDED
(1-5 min). Models: wan2.7-t2v / wan2.7-i2v / wan2.7-r2v / wan2.7-videoedit.
Docs: https://www.alibabacloud.com/help/en/model-studio/text-to-video-api-reference
"""
from __future__ import annotations

import os
import time
from typing import Callable, Optional

import httpx

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
VIDEO_BASE_URL = os.getenv("QWEN_VIDEO_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")
WAN_T2V_MODEL = os.getenv("WAN_T2V_MODEL", "wan2.7-t2v")

_SYNTH = "/services/aigc/video-generation/video-synthesis"


class VideoError(RuntimeError):
    """Wan video task creation/polling failed."""


def _auth() -> dict:
    if not QWEN_API_KEY:
        raise VideoError("QWEN_API_KEY not configured")
    return {"Authorization": f"Bearer {QWEN_API_KEY}"}


def create_task(
    prompt: str,
    model: Optional[str] = None,
    size: str = "1280*720",
    extra_input: Optional[dict] = None,
    client: Optional[httpx.Client] = None,
    timeout: float = 60.0,
) -> str:
    """Create an async video-synthesis task; return its task_id."""
    headers = {**_auth(), "X-DashScope-Async": "enable", "Content-Type": "application/json"}
    inp = {"prompt": prompt}
    if extra_input:
        inp.update(extra_input)
    payload = {"model": model or WAN_T2V_MODEL, "input": inp, "parameters": {"size": size}}
    owns = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        r = client.post(f"{VIDEO_BASE_URL}{_SYNTH}", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPError as e:
        raise VideoError(f"create_task failed: {e}") from e
    finally:
        if owns:
            client.close()
    task_id = (data.get("output") or {}).get("task_id")
    if not task_id:
        raise VideoError(f"no task_id in response: {data}")
    return task_id


def get_task(task_id: str, client: Optional[httpx.Client] = None, timeout: float = 60.0) -> dict:
    """Fetch task status/result JSON."""
    owns = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        r = client.get(f"{VIDEO_BASE_URL}/tasks/{task_id}", headers=_auth())
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise VideoError(f"get_task failed: {e}") from e
    finally:
        if owns:
            client.close()


def poll(
    task_id: str,
    interval: float = 10.0,
    max_wait: float = 420.0,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Poll until SUCCEEDED -> return video_url; FAILED/CANCELED or timeout -> raise."""
    waited = 0.0
    while waited <= max_wait:
        out = get_task(task_id).get("output") or {}
        status = out.get("task_status", "UNKNOWN")
        if status == "SUCCEEDED":
            url = out.get("video_url")
            if not url:
                raise VideoError(f"task succeeded but no video_url: {out}")
            return url
        if status in ("FAILED", "CANCELED"):
            raise VideoError(f"task {status}: {out}")
        sleep(interval)
        waited += interval
    raise VideoError(f"task {task_id} timed out after {max_wait}s")


def generate(prompt: str, model: Optional[str] = None, size: str = "1280*720", **poll_kw) -> str:
    """Convenience: create + poll -> video_url. Requires QWEN_API_KEY."""
    return poll(create_task(prompt, model=model, size=size), **poll_kw)
