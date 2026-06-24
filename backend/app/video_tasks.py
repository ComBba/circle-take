"""Wan / HappyHorse video client (Alibaba Cloud Model Studio / DashScope intl, async).

Verified API (qwencloud-video-generation skill + official docs): submit an async
task (header ``X-DashScope-Async: enable``) -> ``task_id``; poll ``/tasks/{id}`` until
SUCCEEDED. Two endpoints + two resolution params, by mode:

  - t2v / i2v / r2v / vace -> POST .../video-generation/video-synthesis
  - kf2v                   -> POST .../image2video/video-synthesis   (different endpoint)
  - t2v / r2v / vace use ``parameters.size`` ("1280*720"); i2v / kf2v use
    ``parameters.resolution`` ("720P"). Using the wrong one fails the API.

Reference conditioning (the Identity-Lock reshoot) goes in ``input``: i2v=img_url,
kf2v=first_frame_url(+last_frame_url), r2v=reference_urls, vace=function(+ref_images_url).

Model IDs are centralized in .env (latest, free-tier-available): wan2.7-t2v, wan2.7-i2v,
wan2.7-r2v, wan2.2-kf2v-flash, wan2.1-vace-plus. The key is supplied per call by
config.qwen_key() (BYOK header or env). Docs:
https://www.alibabacloud.com/help/en/model-studio/
"""
from __future__ import annotations

import os
import time
from typing import Any, Callable, List, Optional

import httpx

from . import config

VIDEO_BASE_URL = os.getenv("QWEN_VIDEO_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")

# Latest model IDs with free-tier quota (verified via `qwencloud usage free-tier`).
# NOTE: wan2.7-t2v's 50s free quota is already spent; override WAN_T2V_MODEL (e.g.
# wan2.1-t2v-turbo, 200s free) via env when generating fresh t2v on the free tier.
WAN_T2V_MODEL = os.getenv("WAN_T2V_MODEL", "wan2.7-t2v")
WAN_I2V_MODEL = os.getenv("WAN_I2V_MODEL", "wan2.7-i2v")
WAN_R2V_MODEL = os.getenv("WAN_R2V_MODEL", "wan2.7-r2v")
WAN_KF2V_MODEL = os.getenv("WAN_KF2V_MODEL", "wan2.2-kf2v-flash")
WAN_VACE_MODEL = os.getenv("WAN_VIDEOEDIT_MODEL", "wan2.1-vace-plus")

# Endpoints (paths under VIDEO_BASE_URL).
_SYNTH = "/services/aigc/video-generation/video-synthesis"   # t2v, i2v, r2v, vace
_KF2V_SYNTH = "/services/aigc/image2video/video-synthesis"   # kf2v only

# Modes whose resolution is set via parameters.resolution (all others use .size).
_RESOLUTION_MODES = {"i2v", "kf2v"}


class VideoError(RuntimeError):
    """Wan video task creation/polling failed."""


def _auth() -> dict:
    key = config.qwen_key()
    if not key:
        raise VideoError("Qwen API key not provided")
    return {"Authorization": f"Bearer {key}"}


def _endpoint_for(mode: str) -> str:
    return _KF2V_SYNTH if mode == "kf2v" else _SYNTH


def _post_task(
    endpoint: str,
    payload: dict,
    client: Optional[httpx.Client] = None,
    timeout: float = 60.0,
) -> str:
    """POST an async video-synthesis task; return its task_id."""
    headers = {**_auth(), "X-DashScope-Async": "enable", "Content-Type": "application/json"}
    owns = client is None
    client = client or httpx.Client(timeout=timeout)
    try:
        r = client.post(f"{VIDEO_BASE_URL}{endpoint}", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPError as e:
        raise VideoError(f"submit failed: {e}") from e
    finally:
        if owns:
            client.close()
    task_id = (data.get("output") or {}).get("task_id")
    if not task_id:
        raise VideoError(f"no task_id in response: {data}")
    return task_id


def create_task(
    prompt: str,
    model: Optional[str] = None,
    size: str = "1280*720",
    extra_input: Optional[dict] = None,
    client: Optional[httpx.Client] = None,
    timeout: float = 60.0,
) -> str:
    """Create an async t2v task; return its task_id (backward-compatible helper)."""
    inp: dict[str, Any] = {"prompt": prompt}
    if extra_input:
        inp.update(extra_input)
    payload = {"model": model or WAN_T2V_MODEL, "input": inp, "parameters": {"size": size}}
    return _post_task(_SYNTH, payload, client=client, timeout=timeout)


def submit_video(
    mode: str,
    prompt: str,
    *,
    model: str,
    img_url: Optional[str] = None,
    first_frame_url: Optional[str] = None,
    last_frame_url: Optional[str] = None,
    reference_urls: Optional[List[str]] = None,
    ref_images_url: Optional[List[str]] = None,
    function: Optional[str] = None,
    size: str = "1280*720",
    resolution: str = "720P",
    duration: Optional[int] = None,
    shot_type: Optional[str] = None,
    extra_input: Optional[dict] = None,
    extra_params: Optional[dict] = None,
    client: Optional[httpx.Client] = None,
    timeout: float = 60.0,
) -> str:
    """Submit any Wan video mode with the correct endpoint + input/parameters shape.

    Reference field by mode: i2v=img_url; kf2v=first_frame_url(+last_frame_url);
    r2v=reference_urls; vace=function(+ref_images_url). i2v/kf2v use ``resolution``,
    every other mode uses ``size`` (using the wrong one fails the API). Returns task_id.
    """
    inp: dict[str, Any] = {"prompt": prompt}
    if img_url:
        inp["img_url"] = img_url
    if first_frame_url:
        inp["first_frame_url"] = first_frame_url
    if last_frame_url:
        inp["last_frame_url"] = last_frame_url
    if reference_urls:
        inp["reference_urls"] = reference_urls
    if ref_images_url:
        inp["ref_images_url"] = ref_images_url
    if function:
        inp["function"] = function
    if extra_input:
        inp.update(extra_input)

    params: dict[str, Any] = {}
    if mode in _RESOLUTION_MODES:
        params["resolution"] = resolution
    else:
        params["size"] = size
    if duration is not None:
        params["duration"] = duration
    if shot_type:
        params["shot_type"] = shot_type
    if extra_params:
        params.update(extra_params)

    payload = {"model": model, "input": inp, "parameters": params}
    return _post_task(_endpoint_for(mode), payload, client=client, timeout=timeout)


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
    """Convenience: create + poll -> video_url. Requires a Qwen key."""
    return poll(create_task(prompt, model=model, size=size), **poll_kw)
