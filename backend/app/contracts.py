"""Qwen contract builders (Phase 2.2): brief -> Actor/Style/Story contracts.

Each returns a schema-validated Pydantic object via qwen_json. Live calls need
QWEN_API_KEY; endpoints fall back to fixtures in non-live mode.
"""
from __future__ import annotations

from typing import Any, Dict

from . import qwen_client
from .schemas import ActorContracts, StoryContract, StyleContract

ACTOR_SYSTEM = (
    "You are a character designer for an original stop-motion micro-drama. "
    "Use only original, fictional characters (no real people or third-party IP)."
)
STYLE_SYSTEM = "You define the production style grammar (Style Contract) as concrete, checkable rules."
STORY_SYSTEM = (
    "You are Scripty, a showrunner. Turn a brief into a tight 4-beat episode: "
    "hook, conflict, reversal, button."
)


def _fmt(brief: Dict[str, Any]) -> str:
    return f"title={brief.get('title')}; logline={brief.get('logline')}; cast={brief.get('cast')}"


def build_actor_contracts(brief: Dict[str, Any], retries: int = 1) -> ActorContracts:
    user = (
        "Brief: " + _fmt(brief) + "\n"
        "For each cast member return actor_id, display_name, role, fixed_markers "
        "(must-keep identity), forbidden_drift (must-not), motion_signature. "
        'JSON shape: {"actors": [ ... ]}.'
    )
    return qwen_client.qwen_json(ACTOR_SYSTEM, user, ActorContracts, retries=retries)


def build_style_contract(brief: Dict[str, Any], retries: int = 1) -> StyleContract:
    user = (
        "Brief: " + _fmt(brief) + "\n"
        f"Style id hint: {brief.get('style_contract_id', 'clay_stop_motion_mvp')}. "
        'Return {"style_id": ..., "rules": [concrete production rules]}.'
    )
    return qwen_client.qwen_json(STYLE_SYSTEM, user, StyleContract, retries=retries)


def build_story_contract(brief: Dict[str, Any], retries: int = 1) -> StoryContract:
    user = (
        "Brief: " + _fmt(brief) + "\n"
        'Return {"title": ..., "beats": {"hook":..,"conflict":..,"reversal":..,"button":..}, '
        '"tone": .., "runtime_seconds": 15}.'
    )
    return qwen_client.qwen_json(STORY_SYSTEM, user, StoryContract, retries=retries)
