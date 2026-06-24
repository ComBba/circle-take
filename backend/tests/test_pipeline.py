"""Unit tests for the live orchestration (app.pipeline) with Qwen/Wan/OSS mocked.

No network, no credits: every external boundary (Qwen builders, Wan task API,
video download, OSS upload, ffmpeg) is monkeypatched, so we test the orchestration
logic and the async take state machine deterministically.
"""
import os
import tempfile

import pytest
from app import config, pipeline
from app.deps import get_store
from app.main import app
from app.store import Store
from fastapi.testclient import TestClient


class _M:
    """Stand-in for a Pydantic model: only model_dump() is used downstream."""

    def __init__(self, d):
        self._d = d

    def model_dump(self):
        return self._d


def _store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Store(path)


def _stub_text(monkeypatch):
    monkeypatch.setattr(
        pipeline.contracts, "build_actor_contracts",
        lambda b: _M({"actors": [{"display_name": "Luna", "fixed_markers": ["red ribbon"]}]}),
    )
    monkeypatch.setattr(pipeline.contracts, "build_style_contract", lambda b: _M({"rules": ["clay"]}))
    monkeypatch.setattr(pipeline.contracts, "build_story_contract", lambda b: _M({"beats": {}}))
    monkeypatch.setattr(pipeline.storyboard, "build_storyboard", lambda s: _M({"shots": []}))
    monkeypatch.setattr(pipeline.storyboard, "build_shot_risk_ledger", lambda s, a: _M({"risks": []}))


def test_generate_text_stores_five_artifacts(monkeypatch):
    _stub_text(monkeypatch)
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    pipeline.generate_text(store, eid, {"title": "X"})
    assert store.get_artifact(eid, "actor_contracts")["actors"][0]["display_name"] == "Luna"
    assert store.get_artifact(eid, "style_contract") == {"rules": ["clay"]}
    assert store.get_artifact(eid, "shot_risk_ledger") == {"risks": []}


def test_start_take_marks_pending(monkeypatch):
    monkeypatch.setattr(pipeline.video_tasks, "create_task", lambda *a, **k: "task-123")
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    m = pipeline.start_take(store, eid, 1, "prompt")
    assert m == store.get_artifact(eid, "take_1")
    assert m["status"] == "pending" and m["task_id"] == "task-123" and m["source"] == "live"


def test_poll_take_succeeds_finalizes(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "take_1", {"source": "live", "status": "pending", "task_id": "t1"})
    monkeypatch.setattr(
        pipeline.video_tasks, "get_task",
        lambda tid: {"output": {"task_status": "SUCCEEDED", "video_url": "https://wan/v.mp4"}},
    )
    monkeypatch.setattr(pipeline.httpx, "get", lambda url, timeout=0: type("R", (), {"content": b"vid"})())
    monkeypatch.setattr(pipeline, "_extract_frame_data_url", lambda data: "data:image/png;base64,AAA")
    out = pipeline.poll_take(store, eid, 1)
    assert out["status"] == "succeeded"
    assert out["video_url"] == "https://wan/v.mp4"  # caller's own DashScope URL; nothing stored
    assert out["frame_data_url"] == "data:image/png;base64,AAA"
    assert store.get_artifact(eid, "take_1")["status"] == "succeeded"


def test_poll_take_still_running_stays_pending(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "take_1", {"source": "live", "status": "pending", "task_id": "t1"})
    monkeypatch.setattr(pipeline.video_tasks, "get_task", lambda tid: {"output": {"task_status": "RUNNING"}})
    assert pipeline.poll_take(store, eid, 1)["status"] == "pending"


def test_poll_take_failed(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "take_1", {"source": "live", "status": "pending", "task_id": "t1"})
    monkeypatch.setattr(pipeline.video_tasks, "get_task", lambda tid: {"output": {"task_status": "FAILED"}})
    out = pipeline.poll_take(store, eid, 1)
    assert out["status"] == "failed" and out["error"] == "FAILED"


def test_review_requires_take1_frame(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    with pytest.raises(pipeline.PipelineNotReady):
        pipeline.review(store, eid)  # no take_1 yet


def test_review_runs_court_on_frame(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "take_1", {"status": "succeeded", "frame_data_url": "data:image/png;base64,AAA"})
    store.put_artifact(eid, "actor_contracts", {"actors": [{"display_name": "Luna"}]})
    store.put_artifact(eid, "style_contract", {"rules": ["clay"]})
    seen = {}

    def fake_judge(shot, frame, ac, style):
        seen["frame"] = frame
        return _M({"shot_id": shot, "verdict": "fail", "violations": [], "repair_action": "reshoot"})

    monkeypatch.setattr(pipeline.continuity_court, "judge", fake_judge)
    v = pipeline.review(store, eid)
    assert v["verdict"] == "fail"
    assert seen["frame"] == "data:image/png;base64,AAA"  # the real frame went to the court
    assert store.get_artifact(eid, "continuity_verdict")["verdict"] == "fail"


def _capture_submit(monkeypatch, seen):
    def fake_submit(mode, prompt, *, model, **ref):
        seen.update(mode=mode, model=model, ref=ref)
        return "task-2"

    monkeypatch.setattr(pipeline.video_tasks, "submit_video", fake_submit)


def test_reshoot_no_reference_falls_back_to_t2v(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "continuity_verdict", {"shot_id": "S02", "violations": [{"detail": "no ribbon"}]})
    store.put_artifact(eid, "actor_contracts", {"actors": [{"display_name": "Luna", "fixed_markers": ["red ribbon"]}]})
    seen = {}
    _capture_submit(monkeypatch, seen)
    pipeline.reshoot(store, eid)
    assert "RESHOOT S02 ONLY" in store.get_artifact(eid, "reshoot_spell")
    t2 = store.get_artifact(eid, "take_2")
    assert t2["status"] == "pending" and t2["task_id"] == "task-2"
    assert seen["mode"] == "t2v"  # no locked reference -> plain t2v
    assert store.get_artifact(eid, "reshoot_route")["mode"] == "t2v"


def test_reshoot_reference_conditioned_uses_i2v(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "continuity_verdict", {"shot_id": "S02", "violations": []})
    store.put_artifact(eid, "actor_contracts", {"actors": [{"display_name": "Luna"}]})
    store.put_artifact(
        eid, "reference_pack",
        {"actor_id": "luna", "fixed_markers": ["red ribbon"], "reference_image_url": "https://ref/luna.png"},
    )
    seen = {}
    _capture_submit(monkeypatch, seen)
    pipeline.reshoot(store, eid, attempt=0)
    assert seen["mode"] == "i2v"  # reference present -> first-frame identity lock
    assert seen["ref"]["img_url"] == "https://ref/luna.png"
    assert store.get_artifact(eid, "take_2")["mode"] == "i2v"
    assert store.get_artifact(eid, "reshoot_route")["ladder_len"] == 3


def test_reshoot_escalates_to_r2v_on_second_attempt(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "continuity_verdict", {"shot_id": "S02", "violations": []})
    store.put_artifact(eid, "actor_contracts", {"actors": [{"display_name": "Luna"}]})
    store.put_artifact(
        eid, "reference_pack",
        {"actor_id": "luna", "fixed_markers": [], "reference_image_url": "https://ref/luna.png"},
    )
    seen = {}
    _capture_submit(monkeypatch, seen)
    pipeline.reshoot(store, eid, attempt=1)
    assert seen["mode"] == "r2v" and seen["ref"]["reference_urls"] == ["https://ref/luna.png"]


def test_gate_decision_approve_escalate_quarantine():
    g_pass = {"identity_score": 90, "style_score": 88, "prop_score": 91}
    g_fail = {"identity_score": 20, "style_score": 80, "prop_score": 95}
    assert pipeline.gate_decision(g_pass, 0, 3, 85) == "approve"
    assert pipeline.gate_decision(g_fail, 0, 3, 85) == "escalate"  # rungs remain
    assert pipeline.gate_decision(g_fail, 2, 3, 85) == "quarantine"  # ladder exhausted


def _ref_episode():
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "continuity_verdict", {"shot_id": "S02", "violations": []})
    store.put_artifact(eid, "actor_contracts", {"actors": [{"display_name": "Luna"}]})
    store.put_artifact(
        eid, "reference_pack",
        {"actor_id": "luna", "fixed_markers": [], "reference_image_url": "https://ref/luna.png"},
    )
    return store, eid


def test_reshoot_live_honors_scripty_choice(monkeypatch):
    from app.schemas import RepairDecision
    store, eid = _ref_episode()
    monkeypatch.setattr(pipeline.config, "is_live_request", lambda: True)
    monkeypatch.setattr(
        pipeline.scripty, "decide_repair",
        lambda verdict, modes, prior_gate=None: RepairDecision(
            chosen_route="kf2v", reasoning="lock both endpoints", expected_fix="ribbon"),
    )
    seen = {}
    _capture_submit(monkeypatch, seen)
    pipeline.reshoot(store, eid, attempt=0)
    assert seen["mode"] == "kf2v"  # Scripty overrode the default i2v at attempt 0
    dec = store.get_artifact(eid, "scripty_decisions")["decisions"][0]
    assert dec["chosen_route"] == "kf2v" and "lock" in dec["reasoning"]


def test_reshoot_live_falls_back_when_scripty_errors(monkeypatch):
    store, eid = _ref_episode()
    monkeypatch.setattr(pipeline.config, "is_live_request", lambda: True)

    def boom(*a, **k):
        raise RuntimeError("qwen down")

    monkeypatch.setattr(pipeline.scripty, "decide_repair", boom)
    seen = {}
    _capture_submit(monkeypatch, seen)
    pipeline.reshoot(store, eid, attempt=0)
    assert seen["mode"] == "i2v"  # deterministic ladder fallback (attempt 0)


def test_memory_stage_requires_take2(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    with pytest.raises(pipeline.PipelineNotReady):
        pipeline.memory_stage(store, eid)


def test_memory_stage_runs_gate_and_memory(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "take_2", {"status": "succeeded", "frame_data_url": "data:image/png;base64,BBB"})
    store.put_artifact(eid, "actor_contracts", {"actors": []})
    store.put_artifact(eid, "style_contract", {"rules": []})
    monkeypatch.setattr(
        pipeline.anchor_gate, "evaluate",
        lambda shot, frame, ac, style: _M(
            {"shot_id": shot, "identity_score": 92, "style_score": 90, "prop_score": 95, "anchor_status": "approved"}
        ),
    )
    assert pipeline.memory_stage(store, eid) == "approve"
    assert store.get_artifact(eid, "anchor_gate")["anchor_status"] == "approved"
    assert store.get_artifact(eid, "red_thread_memory")["auto_greenlight"]["episode_2_title"] == "The Delivery Box"


def _gate_scores(monkeypatch, scores):
    monkeypatch.setattr(
        pipeline.anchor_gate, "evaluate",
        lambda shot, frame, ac, style: _M({"shot_id": shot, **scores, "anchor_status": "x"}),
    )


def _take2_episode():
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "take_2", {"status": "succeeded", "frame_data_url": "data:image/png;base64,BBB"})
    store.put_artifact(eid, "actor_contracts", {"actors": []})
    store.put_artifact(eid, "style_contract", {"rules": []})
    return store, eid


def test_memory_stage_escalates_below_threshold_with_rungs_left(monkeypatch):
    store, eid = _take2_episode()
    store.put_artifact(eid, "reshoot_route", {"attempt": 0, "ladder_len": 3})
    _gate_scores(monkeypatch, {"identity_score": 15, "style_score": 90, "prop_score": 92})
    assert pipeline.memory_stage(store, eid) == "escalate"
    assert store.get_artifact(eid, "red_thread_memory") is None  # not greenlit
    assert store.get_artifact(eid, "gate_decision")["decision"] == "escalate"


def test_memory_stage_quarantines_when_ladder_exhausted(monkeypatch):
    store, eid = _take2_episode()
    store.put_artifact(eid, "reshoot_route", {"attempt": 2, "ladder_len": 3})
    _gate_scores(monkeypatch, {"identity_score": 15, "style_score": 90, "prop_score": 92})
    assert pipeline.memory_stage(store, eid) == "quarantine"  # honest refusal stays real
    assert store.get_artifact(eid, "red_thread_memory") is None


# --- endpoint wiring: live mode routes to the pipeline ---
def _live_client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.dependency_overrides[get_store] = lambda: Store(path)
    monkeypatch.setattr(config, "is_live_request", lambda: True)  # force the live branch
    return TestClient(app)  # BYOK: anonymous, no auth header


def test_generate_endpoint_live_routes_to_pipeline(monkeypatch):
    calls = []

    def stub_start(s, e, n, p):
        s.put_artifact(e, f"take_{n}", {"status": "pending"})

    monkeypatch.setattr(pipeline, "generate_text", lambda s, e, b: calls.append("text"))
    monkeypatch.setattr(pipeline, "start_take", stub_start)
    c = _live_client(monkeypatch)
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate")
    assert r.status_code == 200 and r.json()["state"] == "TAKE_1_READY"
    assert calls == ["text"]
    assert r.json()["artifacts"]["take_1"]["status"] == "pending"
    app.dependency_overrides.clear()


def test_review_endpoint_409_when_take_not_ready(monkeypatch):
    def stub_start(s, e, n, p):
        s.put_artifact(e, f"take_{n}", {"status": "pending"})

    monkeypatch.setattr(pipeline, "generate_text", lambda s, e, b: None)
    monkeypatch.setattr(pipeline, "start_take", stub_start)

    def not_ready(s, e):
        raise pipeline.PipelineNotReady("Take 1 still generating")

    monkeypatch.setattr(pipeline, "review", not_ready)
    c = _live_client(monkeypatch)
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    c.post(f"/api/episodes/{eid}/generate")
    r = c.post(f"/api/episodes/{eid}/review")
    assert r.status_code == 409 and "generating" in r.json()["detail"]
    app.dependency_overrides.clear()


def test_state_response_strips_frame_data_url(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_text", lambda s, e, b: None)
    monkeypatch.setattr(pipeline, "start_take", lambda s, e, n, p: None)
    c = _live_client(monkeypatch)
    eid = c.post("/api/episodes", json={"title": "X"}).json()["episode_id"]
    store = app.dependency_overrides[get_store]()
    store.put_artifact(
        eid, "take_1",
        {"status": "succeeded", "video_url": "https://oss/v.mp4", "frame_data_url": "data:image/png;base64,AAA"},
    )
    t1 = c.get(f"/api/episodes/{eid}").json()["artifacts"]["take_1"]
    assert t1["video_url"] == "https://oss/v.mp4"
    assert "frame_data_url" not in t1  # heavy internal field never shipped
    app.dependency_overrides.clear()


def test_state_response_resigns_oss_key(monkeypatch):
    from app import oss_storage
    monkeypatch.setattr(oss_storage, "signed_url", lambda key, **k: "https://signed/" + key)
    monkeypatch.setattr(pipeline, "generate_text", lambda s, e, b: None)
    monkeypatch.setattr(pipeline, "start_take", lambda s, e, n, p: None)
    c = _live_client(monkeypatch)
    eid = c.post("/api/episodes", json={"title": "X"}).json()["episode_id"]
    store = app.dependency_overrides[get_store]()
    store.put_artifact(
        eid, "take_1",
        {"status": "succeeded", "oss_key": "live/x/take1.mp4", "video_url": "stale-403-url",
         "frame_data_url": "data:image/png;base64,AAA"},
    )
    t1 = c.get(f"/api/episodes/{eid}").json()["artifacts"]["take_1"]
    assert t1["video_url"] == "https://signed/live/x/take1.mp4"  # re-signed fresh, not the stale url
    assert "frame_data_url" not in t1
    app.dependency_overrides.clear()
