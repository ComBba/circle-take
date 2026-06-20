"""Qwen storyboard + shot-risk builders (Phase 2.2)."""
from __future__ import annotations

from typing import Any, Dict

from . import qwen_client
from .schemas import ShotRiskLedger, StoryboardSlate

SLATE_SYSTEM = "You are a storyboard artist. Produce 3-5 shots that cover the episode beats."
RISK_SYSTEM = "You score per-shot identity/prop/style risk before generation; be specific."


def build_storyboard(story_contract: Dict[str, Any], retries: int = 1) -> StoryboardSlate:
    beats = story_contract.get("beats", story_contract)
    user = (
        f"Episode beats: {beats}\n"
        'Return {"shots": [{"shot_id": "S01", "time": "0-3s", "action": ...}, ...]} with 3-5 shots.'
    )
    return qwen_client.qwen_json(SLATE_SYSTEM, user, StoryboardSlate, retries=retries)


def build_shot_risk_ledger(
    slate: Dict[str, Any], actor_contracts: Dict[str, Any], retries: int = 1
) -> ShotRiskLedger:
    markers = [(a.get("display_name"), a.get("fixed_markers")) for a in actor_contracts.get("actors", [])]
    user = (
        f"Shots: {slate.get('shots', slate)}\n"
        f"Actor fixed markers: {markers}\n"
        'Return {"risks": [{"shot_id":..,"risk_level":"low|medium|high","route":..,'
        '"risk_reasons":[..],"mitigation":[..]}]}.'
    )
    return qwen_client.qwen_json(RISK_SYSTEM, user, ShotRiskLedger, retries=retries)
