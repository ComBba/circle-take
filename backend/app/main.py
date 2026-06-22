"""Circle Take API — golden-path orchestrator.

Fixture-first (Phase 1): each endpoint loads the corresponding golden-path
artifact and advances the episode state machine. Phase 2-3 replace the fixture
loads with real Qwen/Wan calls behind APP_ENV=live (see docs/PLAN.md).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import auth, config, pipeline
from .deps import get_store
from .schemas import (
    EpisodeBrief,
    EpisodeState,
    LoginRequest,
    ProductionReport,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from .state import ORDER, EpisodeStatus
from .store import Store

app = FastAPI(title="Circle Take API", version="0.1.0")

# Authenticated-user dependency (401 if no/invalid bearer token).
CurrentUser = Annotated[dict, Depends(auth.get_current_user)]

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
    # Show the real Wan clip whenever it is bundled (so the deployed demo plays it),
    # not only in full live mode.
    if (LIVE / f"take{n}_S02.mp4").exists():
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


def _require_owned(store: Store, eid: str, user: dict) -> dict:
    """404 (not 403) if the episode is missing or owned by another user."""
    ep = store.get_episode(eid)
    if ep is None or ep.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="episode not found")
    return ep


@app.get("/")
def root():
    # Land visitors (and judges hitting the bare URL) directly on the demo UI.
    return RedirectResponse(url="/ui/")


@app.get("/health")
def health():
    return {"status": "ok", "service": "circle-take", "mode": config.app_env()}


# --- Auth ---
@app.post("/api/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest, store: Store = Depends(get_store)):
    uid = store.create_user(req.email, auth.hash_password(req.password))
    if uid is None:
        raise HTTPException(status_code=409, detail="email already registered")
    return TokenResponse(access_token=auth.create_access_token(uid))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, store: Store = Depends(get_store)):
    user = store.get_user_by_email(req.email)
    if user is None or not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid email or password")
    return TokenResponse(access_token=auth.create_access_token(user["id"]))


@app.get("/api/auth/me", response_model=UserPublic)
def me(user: CurrentUser):
    return UserPublic(id=user["id"], email=user["email"])


# --- Episodes (per-user) ---
@app.post("/api/episodes", response_model=EpisodeState)
def create_episode(brief: EpisodeBrief, user: CurrentUser, store: Store = Depends(get_store)):
    eid = store.create_episode(
        brief.title or "The Last Alarm", EpisodeStatus.DRAFT.value, user_id=user["id"]
    )
    store.put_artifact(eid, "brief", brief.model_dump())
    return _state(store, eid)


@app.get("/api/episodes", response_model=list[EpisodeState])
def list_episodes(user: CurrentUser, store: Store = Depends(get_store)):
    return [
        EpisodeState(
            episode_id=ep["episode_id"],
            state=ep["state"],
            title=ep["title"],
            artifacts={},
        )
        for ep in store.list_episodes(user["id"])
    ]


@app.get("/api/episodes/{eid}", response_model=EpisodeState)
def get_episode(eid: str, user: CurrentUser, store: Store = Depends(get_store)):
    _require_owned(store, eid, user)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/generate", response_model=EpisodeState)
def generate(eid: str, user: CurrentUser, store: Store = Depends(get_store)):
    """Contracts + storyboard + risk ledger + Take 1.

    Live mode (APP_ENV=live + key) calls real Qwen for the text contracts and
    kicks off a real Wan Take 1 render (async — poll /take/1/poll). Fixture mode
    loads golden-path artifacts so the regression suite stays deterministic.
    """
    _require_owned(store, eid, user)
    if config.is_live():
        pipeline.generate_text(store, eid, store.get_artifact(eid, "brief") or {})
        pipeline.start_take(store, eid, 1, pipeline.FAIL_PROMPT)
    else:
        store.put_artifact(eid, "actor_contracts", _resolve_json("actor_contracts.json"))
        store.put_artifact(eid, "style_contract", _resolve_json("style_contract.json"))
        store.put_artifact(eid, "story_contract", _resolve_json("story_contract.json"))
        store.put_artifact(eid, "storyboard_slate", _resolve_json("storyboard_slate.json"))
        store.put_artifact(eid, "shot_risk_ledger", _resolve_json("shot_risk_ledger.json"))
        store.put_artifact(eid, "take_1", _take_marker(1))
    _advance_to(store, eid, EpisodeStatus.TAKE_1_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/take/{n}/poll", response_model=EpisodeState)
def poll_take(eid: str, n: int, user: CurrentUser, store: Store = Depends(get_store)):
    """Advance a pending Wan take (live mode). Safe to call repeatedly."""
    _require_owned(store, eid, user)
    if n not in (1, 2):
        raise HTTPException(status_code=404, detail="unknown take")
    if config.is_live():
        pipeline.poll_take(store, eid, n)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/review", response_model=EpisodeState)
def review(eid: str, user: CurrentUser, store: Store = Depends(get_store)):
    """Continuity Court verdict. Live mode sends Take 1's real frame to Qwen vision."""
    _require_owned(store, eid, user)
    if config.is_live():
        try:
            pipeline.review(store, eid)
        except pipeline.PipelineNotReady as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
    else:
        store.put_artifact(
            eid, "continuity_verdict",
            _resolve_json("continuity_verdict_before.json", "continuity_verdict.json"),
        )
    _advance_to(store, eid, EpisodeStatus.CUT_REQUIRED)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/reshoot", response_model=EpisodeState)
def reshoot(eid: str, user: CurrentUser, store: Store = Depends(get_store)):
    _require_owned(store, eid, user)
    if config.is_live():
        pipeline.reshoot(store, eid)
    else:
        store.put_artifact(eid, "reshoot_spell", _resolve_text("reshoot_spell.txt"))
        store.put_artifact(eid, "continuity_verdict_after", _resolve_json("continuity_verdict_after.json"))
        store.put_artifact(eid, "take_2", _take_marker(2))
    _advance_to(store, eid, EpisodeStatus.TAKE_2_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/memory", response_model=EpisodeState)
def memory(eid: str, user: CurrentUser, store: Store = Depends(get_store)):
    _require_owned(store, eid, user)
    if config.is_live():
        try:
            pipeline.memory_stage(store, eid)
        except pipeline.PipelineNotReady as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
    else:
        store.put_artifact(eid, "anchor_gate", _resolve_json("anchor_gate.json"))
        store.put_artifact(eid, "red_thread_memory", _resolve_json("red_thread_memory.json"))
    _advance_to(store, eid, EpisodeStatus.AUTO_GREENLIT)
    return _state(store, eid)


@app.get("/api/episodes/{eid}/report", response_model=ProductionReport)
def report(eid: str, user: CurrentUser, store: Store = Depends(get_store)):
    ep = _require_owned(store, eid, user)
    return ProductionReport(
        episode_id=ep["episode_id"],
        state=ep["state"],
        title=ep["title"],
        artifacts=ep["artifacts"],
    )


_MEDIA_WHITELIST = {"take1_S02.mp4", "take2_S02.mp4", "take1_frame.png", "take2_frame.png"}


@app.get("/api/media/{name}")
def media(name: str):
    """Serve a live-generated clip/frame from artifacts/live (whitelisted; 404 in fixture mode)."""
    if name not in _MEDIA_WHITELIST:
        raise HTTPException(status_code=404, detail="unknown media")
    p = LIVE / name
    if not p.exists():
        raise HTTPException(status_code=404, detail="not generated (run live golden path)")
    return FileResponse(str(p))


# Serve the self-contained demo UI at /ui (mounted last so it never shadows /api or /health).
if FRONTEND.is_dir():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND), html=True), name="ui")
