"""Pydantic v2 contracts for Circle Take.

These models are the single source of truth for the golden-path artifacts in
examples/golden_path/. `extra="ignore"` keeps them forward-compatible with
richer Qwen output while still validating the required shape.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EpisodeBrief(BaseModel):
    title: Optional[str] = "The Last Alarm"
    logline: str = "A broken alarm clock discovers it will be replaced tomorrow."
    cast: List[str] = Field(
        default_factory=lambda: [
            "Luna, a jealous black cat",
            "Broken Alarm Clock",
            "Tired Office Worker",
        ]
    )
    style_contract_id: str = "clay_stop_motion_mvp"


class EpisodeState(BaseModel):
    episode_id: str
    state: str
    title: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)


# --- Continuity Court ---
class ContinuityVerdict(BaseModel):
    model_config = ConfigDict(extra="ignore")
    shot_id: str
    verdict: str
    violations: List[Dict[str, Any]]
    repair_action: str
    memory_policy: Optional[str] = None


class AnchorGateResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    shot_id: str
    identity_score: int
    style_score: int
    prop_score: int
    anchor_status: str


# --- Shot Risk Ledger ---
class ShotRisk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    shot_id: str
    risk_level: str
    route: Optional[str] = None
    risk_reasons: Optional[List[str]] = None
    mitigation: Optional[List[str]] = None


class ShotRiskLedger(BaseModel):
    model_config = ConfigDict(extra="ignore")
    risks: List[ShotRisk]


# --- Red-Thread Memory ---
class StoryMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    new_fact: str
    relationship_change: str
    open_thread: str


class VisualMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    approved_anchor: str
    known_failure: str
    future_constraint: str


class AutoGreenlight(BaseModel):
    model_config = ConfigDict(extra="ignore")
    episode_2_title: str
    cold_open: str


class RedThreadMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    story_memory: StoryMemory
    visual_memory: VisualMemory
    auto_greenlight: Optional[AutoGreenlight] = None


# --- Production Report (aggregate export) ---
class ProductionReport(BaseModel):
    episode_id: str
    state: str
    title: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)
