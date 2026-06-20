from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class EpisodeBrief(BaseModel):
    title: Optional[str] = "The Last Alarm"
    logline: str = "A broken alarm clock discovers it will be replaced tomorrow."
    cast: List[str] = Field(default_factory=lambda: ["Luna, a jealous black cat", "Broken Alarm Clock", "Tired Office Worker"])
    style_contract_id: str = "clay_stop_motion_mvp"

class EpisodeState(BaseModel):
    episode_id: str
    state: str
    title: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)

class ContinuityVerdict(BaseModel):
    shot_id: str
    verdict: str
    violations: List[Dict[str, Any]]
    repair_action: str

class AnchorGateResult(BaseModel):
    shot_id: str
    identity_score: int
    style_score: int
    prop_score: int
    anchor_status: str
