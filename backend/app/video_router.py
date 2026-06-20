"""Generation Route Selector — picks the Wan 2.7 model(s) per shot.

Maps shot risk/role to a logical route, then to concrete model IDs (centralized
in .env). Repair prefers videoedit with an R2V regeneration fallback.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

WAN_T2V = os.getenv("WAN_T2V_MODEL", "wan2.7-t2v")
WAN_I2V = os.getenv("WAN_I2V_MODEL", "wan2.7-i2v")
WAN_R2V = os.getenv("WAN_R2V_MODEL", "wan2.7-r2v")
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
        "videoedit_then_r2v_fallback": [WAN_EDIT, WAN_R2V],
    }.get(route, [WAN_T2V])
