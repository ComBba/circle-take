"""Circle Take API — golden-path orchestrator.

Fixture-first (Phase 1): each endpoint loads the corresponding golden-path
artifact and advances the episode state machine. Phase 2-3 replace the fixture
loads with real Qwen/Wan calls behind APP_ENV=live (see docs/PLAN.md).
"""
from __future__ import annotations

import hmac
import json
from pathlib import Path
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import config, oss_storage, pipeline, ratelimit
from .deps import get_store
from .schemas import EpisodeBrief, EpisodeState, ProductionReport
from .state import ORDER, EpisodeStatus
from .store import Store

app = FastAPI(title="Circle Take API", version="0.1.0")

# BYOK: episodes are anonymous (no accounts). Live runs use the caller's own Qwen key,
# passed per request via the X-Qwen-Key header — never stored or logged.
QwenKey = Annotated[Optional[str], Header(alias="X-Qwen-Key")]
# Judges enter a passcode (published in the Devpost testing instructions) so only they —
# not the public — can spend the owner's key via the capped judge-live path.
JudgeCode = Annotated[Optional[str], Header(alias="X-Judge-Code")]

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


def _demo_take(n: int) -> dict:
    # Canonical demo clips live at OSS demo/; _public_artifacts re-signs the key.
    return {"source": "demo", "status": "succeeded", "shot": "S02", "oss_key": f"demo/take{n}_S02.mp4"}


def _public_artifacts(artifacts: dict) -> dict:
    """Shape artifacts for API responses: drop the heavy base64 Court frame, and
    re-sign each live take's private OSS object into a fresh presigned video_url."""
    out = {}
    for key, val in artifacts.items():
        if isinstance(val, dict):
            if "frame_data_url" in val:
                val = {k: v for k, v in val.items() if k != "frame_data_url"}
            if val.get("oss_key"):
                try:
                    val = {**val, "video_url": oss_storage.signed_url(val["oss_key"])}
                except Exception:
                    pass  # keep the stored fallback (wan_url) if OSS is unavailable
        out[key] = val
    return out


def _state(store: Store, eid: str) -> EpisodeState:
    ep = store.get_episode(eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return EpisodeState(
        episode_id=ep["episode_id"],
        state=ep["state"],
        title=ep["title"],
        artifacts=_public_artifacts(ep["artifacts"]),
    )


def _advance_to(store: Store, eid: str, target: EpisodeStatus) -> None:
    ep = store.get_episode(eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="episode not found")
    current = EpisodeStatus(ep["state"])
    if ORDER.index(target) < ORDER.index(current):
        raise HTTPException(status_code=409, detail=f"cannot move {current.value} -> {target.value}")
    store.update_status(eid, target.value)


@app.get("/")
def root():
    # Land visitors (and judges hitting the bare URL) directly on the demo UI.
    return RedirectResponse(url="/ui/")


@app.get("/health")
def health():
    return {"status": "ok", "service": "circle-take", "mode": config.app_env()}


@app.get("/api/demo")
def demo():
    """Public, no-auth golden-path walkthrough for the landing — read-only fixtures
    plus the canonical demo clips (presigned). Lets anyone watch the loop before sign-in."""
    arts = {
        "brief": _load_json("brief.json"),
        "actor_contracts": _load_json("actor_contracts.json"),
        "style_contract": _load_json("style_contract.json"),
        "story_contract": _load_json("story_contract.json"),
        "storyboard_slate": _load_json("storyboard_slate.json"),
        "shot_risk_ledger": _load_json("shot_risk_ledger.json"),
        "take_1": _demo_take(1),
        "continuity_verdict": _load_json("continuity_verdict_before.json"),
        "reshoot_spell": _load_text("reshoot_spell.txt"),
        "take_2": _demo_take(2),
        "anchor_gate": _load_json("anchor_gate.json"),
        "red_thread_memory": _load_json("red_thread_memory.json"),
    }
    return {
        "episode_id": "demo",
        "state": "AUTO_GREENLIT",
        "title": "The Last Alarm",
        "artifacts": _public_artifacts(arts),
    }


def _effective_live(
    store: Store,
    eid: str,
    x_qwen_key: Optional[str],
    judge_code: Optional[str] = None,
    starting: bool = False,
) -> bool:
    """Resolve the key for this request and report whether to run live.

    Priority: the caller's BYOK key (X-Qwen-Key) > a **passcode-gated**, capped server-side
    judge key (lets judges — who hold the published JUDGE_CODE — run live without their own
    key, owner-funded + rate-limited) > fixtures. The judge key is set only into the
    per-request ContextVar — never stored or returned. A correct passcode + free daily-cap
    slot at /generate marks the episode judge-funded; its later endpoints stay funded
    without re-sending the code. The judge-live path is OFF unless BOTH JUDGE_QWEN_KEY and
    JUDGE_CODE are configured.
    """
    if x_qwen_key:
        config.set_request_key(x_qwen_key)
        return config.is_live_request()
    jkey, expected = config.judge_key(), config.judge_code()
    if jkey and expected:
        funded = bool(store.get_artifact(eid, "judge_funded"))
        code_ok = bool(judge_code) and hmac.compare_digest(judge_code, expected)
        if not funded and starting and code_ok and ratelimit.try_consume(config.judge_daily_cap()):
            store.put_artifact(eid, "judge_funded", True)
            funded = True
        if funded:
            config.set_request_key(jkey)
            return config.is_live_request()
    config.set_request_key(x_qwen_key)  # None -> "" (fixtures unless env is live)
    return config.is_live_request()


def _owned(store: Store, eid: str) -> dict:
    ep = store.get_episode(eid)
    if ep is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return ep


# --- Episodes (anonymous; a Qwen key gates live generation, BYOK) ---
@app.post("/api/episodes", response_model=EpisodeState)
def create_episode(brief: EpisodeBrief, store: Store = Depends(get_store)):
    eid = store.create_episode(brief.title or "The Last Alarm", EpisodeStatus.DRAFT.value)
    store.put_artifact(eid, "brief", brief.model_dump())
    return _state(store, eid)


@app.get("/api/episodes/{eid}", response_model=EpisodeState)
def get_episode(eid: str, store: Store = Depends(get_store)):
    _owned(store, eid)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/generate", response_model=EpisodeState)
def generate(
    eid: str,
    store: Store = Depends(get_store),
    x_qwen_key: QwenKey = None,
    x_judge_code: JudgeCode = None,
):
    """Contracts + storyboard + risk + Take 1.

    With a Qwen key (X-Qwen-Key) this runs real Qwen + Wan; with a valid judge passcode
    (X-Judge-Code) it runs live on the owner-funded capped judge key; otherwise it replays
    the golden-path fixtures (deterministic, key-free).
    """
    _owned(store, eid)
    if _effective_live(store, eid, x_qwen_key, judge_code=x_judge_code, starting=True):
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
def poll_take(eid: str, n: int, store: Store = Depends(get_store), x_qwen_key: QwenKey = None):
    """Advance a pending Wan take (live mode). Safe to call repeatedly."""
    _owned(store, eid)
    if n not in (1, 2):
        raise HTTPException(status_code=404, detail="unknown take")
    if _effective_live(store, eid, x_qwen_key):
        pipeline.poll_take(store, eid, n)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/review", response_model=EpisodeState)
def review(eid: str, store: Store = Depends(get_store), x_qwen_key: QwenKey = None):
    """Continuity Court verdict. Live mode sends Take 1's real frame to Qwen vision."""
    _owned(store, eid)
    if _effective_live(store, eid, x_qwen_key):
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
def reshoot(eid: str, store: Store = Depends(get_store), x_qwen_key: QwenKey = None):
    _owned(store, eid)
    if _effective_live(store, eid, x_qwen_key):
        pipeline.reshoot(store, eid)
    else:
        store.put_artifact(eid, "reshoot_spell", _resolve_text("reshoot_spell.txt"))
        store.put_artifact(eid, "continuity_verdict_after", _resolve_json("continuity_verdict_after.json"))
        store.put_artifact(eid, "take_2", _take_marker(2))
    _advance_to(store, eid, EpisodeStatus.TAKE_2_READY)
    return _state(store, eid)


@app.post("/api/episodes/{eid}/memory", response_model=EpisodeState)
def memory(eid: str, store: Store = Depends(get_store), x_qwen_key: QwenKey = None):
    _owned(store, eid)
    if _effective_live(store, eid, x_qwen_key):
        try:
            decision = pipeline.memory_stage(store, eid)
        except pipeline.PipelineNotReady as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
        if decision == "escalate":
            # Below threshold but ladder rungs remain: reshoot the next route and stay at
            # TAKE_2_READY so the client re-polls Take 2, then calls /memory again.
            route = store.get_artifact(eid, "reshoot_route") or {"attempt": 0}
            pipeline.reshoot(store, eid, attempt=route.get("attempt", 0) + 1)
            return _state(store, eid)
    else:
        store.put_artifact(eid, "anchor_gate", _resolve_json("anchor_gate.json"))
        store.put_artifact(eid, "red_thread_memory", _resolve_json("red_thread_memory.json"))
    # approve (greenlit + remembered) or quarantine (honest refusal, no memory) — both terminal.
    _advance_to(store, eid, EpisodeStatus.AUTO_GREENLIT)
    return _state(store, eid)


@app.get("/api/episodes/{eid}/report", response_model=ProductionReport)
def report(eid: str, store: Store = Depends(get_store)):
    ep = _owned(store, eid)
    return ProductionReport(
        episode_id=ep["episode_id"],
        state=ep["state"],
        title=ep["title"],
        artifacts=_public_artifacts(ep["artifacts"]),
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
