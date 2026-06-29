"""Generation Route Selector — picks the Wan 2.7 model(s) per shot.

Maps shot risk/role to a logical route, then to concrete model IDs (centralized
in .env). Repair prefers videoedit with an R2V regeneration fallback.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

WAN_T2V = os.getenv("WAN_T2V_MODEL", "wan2.7-t2v")
WAN_I2V = os.getenv("WAN_I2V_MODEL", "wan2.7-i2v")
WAN_R2V = os.getenv("WAN_R2V_MODEL", "wan2.7-r2v")
WAN_KF2V = os.getenv("WAN_KF2V_MODEL", "wan2.2-kf2v-flash")
WAN_EDIT = os.getenv("WAN_VIDEOEDIT_MODEL", "wan2.7-videoedit")


def select_route(shot: Dict[str, Any]) -> str:
    """Logical route: t2v | i2v | r2v | videoedit_then_r2v_fallback."""
    if shot.get("repair"):
        return "videoedit_then_r2v_fallback"
    if shot.get("character_critical") or shot.get("risk_level") == "high":
        return "r2v"
    if shot.get("first_or_last_frame"):
        return "i2v"
    return "t2v"


def models_for(route: str) -> List[str]:
    """Ordered model IDs to try for a route (first is preferred, rest are fallbacks)."""
    return {
        "t2v": [WAN_T2V],
        "i2v": [WAN_I2V],
        "r2v": [WAN_R2V],
        "kf2v": [WAN_KF2V],
        "videoedit_then_r2v_fallback": [WAN_EDIT, WAN_R2V],
    }.get(route, [WAN_T2V])


def reshoot_ladder(reference_image_url: Optional[str]) -> List[Dict[str, Any]]:
    """The escalating reshoot route sequence for the Identity-Lock reshoot.

    With a locked reference keyframe, prefer reference-conditioned regeneration
    (i2v first-frame lock -> r2v reference role-play -> kf2v first+last lock); each
    rung carries the ``ref`` kwargs for ``video_tasks.submit_video``. Without a
    reference, there is nothing to lock onto, so fall back to a single t2v rung.
    """
    ref = reference_image_url
    if ref:
        # i2v is the render-verified primary rung (submit_video maps img_url ->
        # input.media[{type:first_frame}] for wan2.7). NOTE: wan2.7-r2v also moved to the
        # unified input.media[] and its subject-reference schema is not yet validated
        # (reference_urls + bare first_frame both rejected) — escalation-only, follow-up.
        return [
            {"mode": "i2v", "model": WAN_I2V, "ref": {"img_url": ref}},
            {"mode": "r2v", "model": WAN_R2V, "ref": {"reference_urls": [ref]}},
            {"mode": "kf2v", "model": WAN_KF2V,
             "ref": {"first_frame_url": ref, "last_frame_url": ref}},
        ]
    return [{"mode": "t2v", "model": WAN_T2V, "ref": {}}]
