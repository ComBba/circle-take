import os
import tempfile

from app.deps import get_store
from app.main import app
from app.store import Store
from fastapi.testclient import TestClient


def _client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.dependency_overrides[get_store] = lambda: Store(path)
    return TestClient(app)


def test_health():
    c = _client()
    assert c.get("/health").json()["status"] == "ok"
    app.dependency_overrides.clear()


def test_full_golden_path_over_fixtures():
    c = _client()
    r = c.post("/api/episodes", json={"title": "The Last Alarm"})
    assert r.status_code == 200
    eid = r.json()["episode_id"]
    assert r.json()["state"] == "DRAFT"

    assert c.post(f"/api/episodes/{eid}/generate").json()["state"] == "TAKE_1_READY"
    assert c.post(f"/api/episodes/{eid}/review").json()["state"] == "CUT_REQUIRED"
    assert c.post(f"/api/episodes/{eid}/reshoot").json()["state"] == "TAKE_2_READY"
    assert c.post(f"/api/episodes/{eid}/memory").json()["state"] == "AUTO_GREENLIT"

    rep = c.get(f"/api/episodes/{eid}/report").json()
    assert rep["state"] == "AUTO_GREENLIT"
    assert rep["artifacts"]["continuity_verdict"]["verdict"] == "fail"
    assert (
        rep["artifacts"]["red_thread_memory"]["auto_greenlight"]["episode_2_title"]
        == "The Delivery Box"
    )
    app.dependency_overrides.clear()


def test_unknown_episode_404():
    c = _client()
    assert c.get("/api/episodes/nope").status_code == 404
    app.dependency_overrides.clear()


def test_ui_served():
    c = _client()
    r = c.get("/ui/")
    assert r.status_code == 200
    assert "Circle Take" in r.text
    app.dependency_overrides.clear()


def test_report_unknown_404():
    c = _client()
    assert c.get("/api/episodes/nope/report").status_code == 404
    app.dependency_overrides.clear()


def test_generate_unknown_404():
    c = _client()
    assert c.post("/api/episodes/nope/generate").status_code == 404
    app.dependency_overrides.clear()


def test_backward_transition_rejected_409():
    c = _client()
    eid = c.post("/api/episodes", json={"title": "X"}).json()["episode_id"]
    for s in ("generate", "review", "reshoot", "memory"):
        c.post(f"/api/episodes/{eid}/{s}")
    # /review targets CUT_REQUIRED, earlier than AUTO_GREENLIT -> backward -> 409
    assert c.post(f"/api/episodes/{eid}/review").status_code == 409
    app.dependency_overrides.clear()
