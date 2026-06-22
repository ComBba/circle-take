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
    monkeypatch.setattr(pipeline, "_oss_put", lambda *a, **k: "https://oss/take1.mp4")
    monkeypatch.setattr(pipeline, "_extract_frame_data_url", lambda data: "data:image/png;base64,AAA")
    out = pipeline.poll_take(store, eid, 1)
    assert out["status"] == "succeeded"
    assert out["video_url"] == "https://oss/take1.mp4"  # OSS preferred (persistent)
    assert out["wan_url"] == "https://wan/v.mp4"
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


def test_reshoot_writes_spell_and_starts_take2(monkeypatch):
    store = _store()
    eid = store.create_episode("X", "DRAFT")
    store.put_artifact(eid, "continuity_verdict", {"shot_id": "S02", "violations": [{"detail": "no ribbon"}]})
    store.put_artifact(eid, "actor_contracts", {"actors": [{"display_name": "Luna", "fixed_markers": ["red ribbon"]}]})
    monkeypatch.setattr(pipeline.video_tasks, "create_task", lambda *a, **k: "task-2")
    pipeline.reshoot(store, eid)
    assert "RESHOOT S02 ONLY" in store.get_artifact(eid, "reshoot_spell")
    assert store.get_artifact(eid, "take_2")["status"] == "pending"


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
    pipeline.memory_stage(store, eid)
    assert store.get_artifact(eid, "anchor_gate")["anchor_status"] == "approved"
    assert store.get_artifact(eid, "red_thread_memory")["auto_greenlight"]["episode_2_title"] == "The Delivery Box"


# --- endpoint wiring: live mode routes to the pipeline ---
def _live_client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.dependency_overrides[get_store] = lambda: Store(path)
    monkeypatch.setattr(config, "is_live", lambda: True)
    c = TestClient(app)
    token = c.post("/api/auth/register", json={"email": "live@circle.take", "password": "password123"}).json()[
        "access_token"
    ]
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c


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
