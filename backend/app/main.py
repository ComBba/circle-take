"""Circle Take API — golden-path orchestrator.

Fixture-first (Phase 1): each endpoint loads the corresponding golden-path
artifact and advances the episode state machine. Phase 2-3 replace the fixture
loads with real Qwen/Wan calls behind APP_ENV=live (see docs/PLAN.md).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException

from .deps import get_store
from .schemas import EpisodeBrief, EpisodeState, ProductionReport
from .state import ORDER, EpisodeStatus
from .store import Store

app = FastAPI(title="Circle Take API", version="0.1.0")

GOLDEN = Path(__file__).resolve().parents[2] / "examples" / "golden_path"


def _load_json(name: str):
    return json.loads((GOLDEN / name).read_text())


def _load_text(name: str) -> str:
    return (GOLDEN / name).read_text()


def _state(store: Store, eid: str) -> EpisodeState:
    ep = store.get_episode(eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return EpisodeState(
        episode_id=ep["episode_id"],
        state=ep["state"],
        title=ep["title"],
        artifacts=ep["artifacts"],
    )


def _advance_to(store: Store, eid: str, target: EpisodeStatus) -> None:
    ep = store.get_episode(eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="episode not found")
    current = EpisodeStatus(ep["state"])
    if ORDER.index(target) < ORDER.index(current):
        raise HTTPException(status_code=409, detail=f"cannot move {current.value} -> {target.value}")
    store.update_status(eid, target.value)


@app.get("/health")
def health():
    return {"status": "ok", "service": "circle-take"}


@app.post("/api/episodes", response_model=EpisodeState)
def create_episode(brief: EpisodeBrief, store: Store = Depends(get_store)):
    eid = store.create_episode(brief.title or "The Last Alarm", EpisodeStatus.DRAFT.value)
    store.put_artifact(eid, "brief", brief.model_dump())
    return _state(store, eid)


@app.get("/api/episodes/{eid}", response_model=EpisodeState)
def get_episode(eid: str, store: Store = Depends(get_store)):
    return _state(store, eid)


@app.post("/api/episodes/{eid}/generate", response_model=EpisodeState)
def generate(eid: str, store: Store = Depends(get_store)):
    """Contracts + storyboard + risk ledger + Take 1.

    Fixture mode loads golden-path artifacts; live mode (Phase 2-3) will call
    Qwen for contracts/storyboard and Wan for Take 1.
    """
    store.put_artifact(eid, "actor_contracts", _load_json("actor_contracts.json"))
    store.put_artifact(eid, "style_contract", _load_json("style_contract.json"))
    store.put_artifact(eid, "story_contract", _load_json("story_contract.json"))
    store.put_artifact(eid, "storyboard_slate", _load_json("storyboard_slate.json"))
    store.put_artifact(eid, "shot_risk_ledger", _load_json("shot_risk_ledger.json"))
    store.put_artifact(eid, "take_1", {"source": "fixture", "pending": "QWEN_API_KEY for live Wan T2V/R2V"})
    _advance_to(store, eid, EpisodeStatus.TAKE_1_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/review", response_model=EpisodeState)
def review(eid: str, store: Store = Depends(get_store)):
    """Continuity Court verdict. Live mode (Phase 2.3) sends a real frame to Qwen vision."""
    store.put_artifact(eid, "continuity_verdict", _load_json("continuity_verdict_before.json"))
    _advance_to(store, eid, EpisodeStatus.CUT_REQUIRED)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/reshoot", response_model=EpisodeState)
def reshoot(eid: str, store: Store = Depends(get_store)):
    store.put_artifact(eid, "reshoot_spell", _load_text("reshoot_spell.txt"))
    store.put_artifact(eid, "continuity_verdict_after", _load_json("continuity_verdict_after.json"))
    store.put_artifact(eid, "take_2", {"source": "fixture", "pending": "QWEN_API_KEY for live Wan videoedit/R2V"})
    _advance_to(store, eid, EpisodeStatus.TAKE_2_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/memory", response_model=EpisodeState)
def memory(eid: str, store: Store = Depends(get_store)):
    store.put_artifact(eid, "anchor_gate", _load_json("anchor_gate.json"))
    store.put_artifact(eid, "red_thread_memory", _load_json("red_thread_memory.json"))
    _advance_to(store, eid, EpisodeStatus.AUTO_GREENLIT)
    return _state(store, eid)


@app.get("/api/episodes/{eid}/report", response_model=ProductionReport)
def report(eid: str, store: Store = Depends(get_store)):
    ep = store.get_episode(eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return ProductionReport(
        episode_id=ep["episode_id"],
        state=ep["state"],
        title=ep["title"],
        artifacts=ep["artifacts"],
    )
