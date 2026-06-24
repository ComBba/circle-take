"""Reference Pack — the locked identity anchors the reshoot conditions on.

The Identity-Lock reshoot needs a reference of the actor WITH its required markers
(e.g. Luna with her red ribbon), not just a text prompt. This module captures that as
a small artifact: the primary actor's id, its fixed markers (text), and a reference
keyframe URL used to condition i2v / r2v / kf2v regeneration. The escalating reshoot
ladder itself lives in ``video_router`` (route selection in one place).
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def build_reference_pack(
    actor_contracts: Dict[str, Any], reference_image_url: Optional[str] = None
) -> Dict[str, Any]:
    """Lock the primary actor's identity: id + fixed markers + reference keyframe URL.

    ``reference_image_url`` is the locked keyframe used to condition the reshoot; when
    absent the reshoot falls back to plain t2v (no mechanical identity lock).
    """
    actors = actor_contracts.get("actors", [])
    primary = actors[0] if actors else {}
    return {
        "actor_id": primary.get("actor_id") or primary.get("display_name", "actor"),
        "fixed_markers": list(primary.get("fixed_markers", [])),
        "reference_image_url": (reference_image_url or "") or None,
    }
