"""Per-request live orchestration: real Qwen3.7 + Wan2.7, stored per episode.

main.py calls these when config.is_live(); otherwise it serves golden-path
fixtures (regression guard). Mirrors scripts/run_golden_path_live.py but driven by
API requests, keyed per episode, and Wan-async-safe:

  generate_text()  -> real Qwen contracts/storyboard/risk (fast, seconds)
  start_take()     -> kicks off a Wan task, stores a {status:"pending"} marker
  poll_take()      -> advances pending -> succeeded (downloads video, mirrors to
                      OSS, extracts a frame as a base64 data-URL the Court can read)
  review()         -> real Qwen-vision Continuity Court on Take 1's frame
  reshoot()        -> reshoot spell + starts Take 2
  memory_stage()   -> real Anchor Gate (vision) on Take 2 + Red-Thread Memory

Frames travel as base64 data-URLs inside the DB artifact so the Court works across
Cloud Run cold starts (no reliance on instance-local files or a public OSS ACL).
"""
from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

import httpx

from . import (
    anchor_gate,
    continuity_court,
    contracts,
    reshoot_spell,
    storyboard,
    video_tasks,
)
from . import memory as memory_mod
from .store import Store

# Demo-failure strategy = Option B (transparent constructed): Take 1 omits Luna's
# ribbon (the Court catches it), Take 2 restores it. Both are real generations.
FAIL_PROMPT = (
    "clay stop-motion, a black clay cat WITHOUT any ribbon hides a small paper ad "
    "under her tail, tabletop miniature set, handmade clay texture, visible fingerprints"
)
FIX_PROMPT = (
    "clay stop-motion, a black clay cat with a bright RED RIBBON and a crooked left ear "
    "hides a small paper ad under her tail, tabletop miniature set, handmade clay texture"
)


class PipelineNotReady(RuntimeError):
    """A live stage needs a Wan take that has not finished generating yet."""


def generate_text(store: Store, eid: str, brief: dict) -> None:
    """Real Qwen text stage: contracts + storyboard + shot risk, stored per episode."""
    actors = contracts.build_actor_contracts(brief).model_dump()
    style = contracts.build_style_contract(brief).model_dump()
    story = contracts.build_story_contract(brief).model_dump()
    slate = storyboard.build_storyboard(story).model_dump()
    risk = storyboard.build_shot_risk_ledger(slate, actors).model_dump()
    store.put_artifact(eid, "actor_contracts", actors)
    store.put_artifact(eid, "style_contract", style)
    store.put_artifact(eid, "story_contract", story)
    store.put_artifact(eid, "storyboard_slate", slate)
    store.put_artifact(eid, "shot_risk_ledger", risk)


def start_take(store: Store, eid: str, n: int, prompt: str) -> dict:
    """Kick off a Wan T2V task; store a pending marker (does not block on render)."""
    task_id = video_tasks.create_task(prompt, model=video_tasks.WAN_T2V_MODEL)
    marker = {"source": "live", "status": "pending", "task_id": task_id, "shot": "S02"}
    store.put_artifact(eid, f"take_{n}", marker)
    return marker


def poll_take(store: Store, eid: str, n: int) -> dict:
    """Advance a pending take: SUCCEEDED -> finalize+store; FAILED -> mark failed."""
    marker = store.get_artifact(eid, f"take_{n}") or {}
    if marker.get("status") != "pending":
        return marker
    out = video_tasks.get_task(marker["task_id"]).get("output") or {}
    status = out.get("task_status", "UNKNOWN")
    if status == "SUCCEEDED":
        marker = _finalize_take(eid, n, marker, out.get("video_url"))
    elif status in ("FAILED", "CANCELED"):
        marker = {**marker, "status": "failed", "error": status}
    store.put_artifact(eid, f"take_{n}", marker)
    return marker


def _finalize_take(eid: str, n: int, marker: dict, wan_url: Optional[str]) -> dict:
    if not wan_url:
        return {**marker, "status": "failed", "error": "no video_url"}
    # BYOK / no-storage: serve the caller's own DashScope signed URL directly and only
    # download the bytes transiently to grab the Court's frame. Nothing is persisted.
    data = httpx.get(wan_url, timeout=180).content
    return {
        "source": "live",
        "status": "succeeded",
        "shot": "S02",
        "video_url": wan_url,
        "frame_data_url": _extract_frame_data_url(data),
    }


def _extract_frame_data_url(video_bytes: bytes) -> Optional[str]:
    """Grab a representative frame as a base64 PNG data-URL (needs ffmpeg in PATH)."""
    with tempfile.TemporaryDirectory() as d:
        vp, fp = Path(d) / "v.mp4", Path(d) / "f.png"
        vp.write_bytes(video_bytes)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(vp), "-vf", "select=eq(n\\,30)",
                 "-vframes", "1", str(fp)],
                check=True, capture_output=True,
            )
            return "data:image/png;base64," + base64.b64encode(fp.read_bytes()).decode()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None


def _contracts(store: Store, eid: str) -> tuple[dict, dict]:
    actors = store.get_artifact(eid, "actor_contracts") or {"actors": []}
    style = store.get_artifact(eid, "style_contract") or {"rules": []}
    return {"actors": actors.get("actors", [])}, style


def review(store: Store, eid: str) -> dict:
    """Real Qwen-vision Continuity Court on Take 1's frame. 409 if take not ready."""
    take1 = store.get_artifact(eid, "take_1") or {}
    frame = take1.get("frame_data_url")
    if not frame:
        raise PipelineNotReady("Take 1 is still generating; poll /take/1/poll first")
    ac, style = _contracts(store, eid)
    verdict = continuity_court.judge("S02", frame, ac, style).model_dump()
    store.put_artifact(eid, "continuity_verdict", verdict)
    return verdict


def reshoot(store: Store, eid: str) -> None:
    """Delta reshoot spell from the verdict, then start the Take 2 render."""
    verdict = store.get_artifact(eid, "continuity_verdict") or {}
    ac, _ = _contracts(store, eid)
    store.put_artifact(eid, "reshoot_spell", reshoot_spell.build_reshoot_spell(verdict, ac))
    start_take(store, eid, 2, FIX_PROMPT)


def memory_stage(store: Store, eid: str) -> None:
    """Real Anchor Gate (vision) on Take 2, then Red-Thread Memory. 409 if not ready."""
    take2 = store.get_artifact(eid, "take_2") or {}
    frame = take2.get("frame_data_url")
    if not frame:
        raise PipelineNotReady("Take 2 is still generating; poll /take/2/poll first")
    ac, style = _contracts(store, eid)
    gate: dict[str, Any] = anchor_gate.evaluate("S02_take_two", frame, ac, style).model_dump()
    store.put_artifact(eid, "anchor_gate", gate)
    store.put_artifact(eid, "red_thread_memory", memory_mod.build_red_thread_memory(gate))
