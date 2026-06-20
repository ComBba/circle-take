"""Circle Take API — golden-path orchestrator.

Fixture-first (Phase 1): each endpoint loads the corresponding golden-path
artifact and advances the episode state machine. Phase 2-3 replace the fixture
loads with real Qwen/Wan calls behind APP_ENV=live (see docs/PLAN.md).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .deps import get_store
from .schemas import EpisodeBrief, EpisodeState, ProductionReport
from .state import ORDER, EpisodeStatus
from .store import Store

app = FastAPI(title="Circle Take API", version="0.1.0")

# Demo CORS — let the static UI (and judges' browsers) call the API from any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GOLDEN = Path(__file__).resolve().parents[2] / "examples" / "golden_path"
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
LIVE = Path(__file__).resolve().parents[2] / "artifacts" / "live"


def _load_json(name: str):
    return json.loads((GOLDEN / name).read_text())


def _load_text(name: str) -> str:
    return (GOLDEN / name).read_text()


def _resolve_json(fixture_name: str, live_name: str | None = None):
    """In live mode, prefer artifacts/live/<live_name>; else the golden-path fixture."""
    if config.is_live():
        p = LIVE / (live_name or fixture_name)
        if p.exists():
            return json.loads(p.read_text())
    return _load_json(fixture_name)


def _resolve_text(fixture_name: str, live_name: str | None = None) -> str:
    if config.is_live():
        p = LIVE / (live_name or fixture_name)
        if p.exists():
            return p.read_text()
    return _load_text(fixture_name)


def _take_marker(n: int):
    if config.is_live() and (LIVE / f"take{n}_S02.mp4").exists():
        return {"source": "live", "video": f"live/take{n}_S02.mp4", "frame": f"live/take{n}_frame.png"}
    return {"source": "fixture", "pending": "QWEN_API_KEY for live Wan"}


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
    return {"status": "ok", "service": "circle-take", "mode": config.app_env()}


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
    store.put_artifact(eid, "actor_contracts", _resolve_json("actor_contracts.json"))
    store.put_artifact(eid, "style_contract", _resolve_json("style_contract.json"))
    store.put_artifact(eid, "story_contract", _resolve_json("story_contract.json"))
    store.put_artifact(eid, "storyboard_slate", _resolve_json("storyboard_slate.json"))
    store.put_artifact(eid, "shot_risk_ledger", _resolve_json("shot_risk_ledger.json"))
    store.put_artifact(eid, "take_1", _take_marker(1))
    _advance_to(store, eid, EpisodeStatus.TAKE_1_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/review", response_model=EpisodeState)
def review(eid: str, store: Store = Depends(get_store)):
    """Continuity Court verdict. Live mode (Phase 2.3) sends a real frame to Qwen vision."""
    store.put_artifact(eid, "continuity_verdict", _resolve_json("continuity_verdict_before.json", "continuity_verdict.json"))
    _advance_to(store, eid, EpisodeStatus.CUT_REQUIRED)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/reshoot", response_model=EpisodeState)
def reshoot(eid: str, store: Store = Depends(get_store)):
    store.put_artifact(eid, "reshoot_spell", _resolve_text("reshoot_spell.txt"))
    store.put_artifact(eid, "continuity_verdict_after", _resolve_json("continuity_verdict_after.json"))
    store.put_artifact(eid, "take_2", _take_marker(2))
    _advance_to(store, eid, EpisodeStatus.TAKE_2_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/memory", response_model=EpisodeState)
def memory(eid: str, store: Store = Depends(get_store)):
    store.put_artifact(eid, "anchor_gate", _resolve_json("anchor_gate.json"))
    store.put_artifact(eid, "red_thread_memory", _resolve_json("red_thread_memory.json"))
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


# Serve the self-contained demo UI at /ui (mounted last so it never shadows /api or /health).
if FRONTEND.is_dir():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND), html=True), name="ui")
