"""Anchor Gate — Qwen-vision scores the repaired keyframe, then approves or quarantines.

Only approved anchors become Red-Thread Memory. Requires QWEN_API_KEY (vision model).
"""
from __future__ import annotations

from typing import Any, Dict

from . import qwen_client
from .schemas import AnchorGateResult

ANCHOR_GATE_SYSTEM = (
    "You are the Anchor Gate. Score the repaired keyframe 0-100 on identity_score, "
    "style_score, and prop_score against the contracts. Set anchor_status to 'approved' "
    "only if every score is at least the threshold, otherwise 'quarantine'."
)


def evaluate(
    shot_id: str,
    frame: str,
    actor_contracts: Dict[str, Any],
    style_contract: Dict[str, Any],
    retries: int = 1,
) -> AnchorGateResult:
    markers = [(a.get("display_name"), a.get("fixed_markers")) for a in actor_contracts.get("actors", [])]
    user = (
        f"shot_id={shot_id}\nScore the repaired frame against the contracts.\n"
        f"Actor fixed markers: {markers}\n"
        f"Style rules: {style_contract.get('rules')}\n"
        "Return {shot_id, identity_score, style_score, prop_score, anchor_status}."
    )
    return qwen_client.qwen_vision_json(ANCHOR_GATE_SYSTEM, frame, user, AnchorGateResult, retries=retries)


def is_approved(result: AnchorGateResult, threshold: int = 85) -> bool:
    """True only if every score meets the threshold."""
    return min(result.identity_score, result.style_score, result.prop_score) >= threshold
