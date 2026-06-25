"""Capped judge live path: BYOK > judge key (rate-limited) > fixture; key never leaks."""
import os
import tempfile

from app import config, pipeline, ratelimit
from app.deps import get_store
from app.main import app
from app.store import Store
from fastapi.testclient import TestClient


def _client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.dependency_overrides[get_store] = lambda: Store(path)
    return TestClient(app)


def _stub_pipeline(monkeypatch, calls):
    monkeypatch.setattr(pipeline, "generate_text", lambda s, e, b: calls.append("text"))
    monkeypatch.setattr(
        pipeline, "start_take", lambda s, e, n, p: s.put_artifact(e, f"take_{n}", {"status": "pending"})
    )


def test_judge_key_funds_live_without_byok(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    monkeypatch.setattr(config, "judge_key", lambda: "jk-secret")
    monkeypatch.setattr(config, "is_live_request", lambda: True)
    ratelimit.reset()
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate")  # no X-Qwen-Key
    assert r.status_code == 200
    assert calls == ["text"]  # judge key funded the live pipeline
    assert r.json()["artifacts"]["judge_funded"] is True
    assert "jk-secret" not in r.text  # the judge key never leaks into the response
    app.dependency_overrides.clear()


def test_byok_overrides_judge_and_leaves_cap_untouched(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    monkeypatch.setattr(config, "judge_key", lambda: "jk-secret")
    monkeypatch.setattr(config, "is_live_request", lambda: True)
    ratelimit.reset()
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate", headers={"X-Qwen-Key": "byok"})
    assert r.status_code == 200 and calls == ["text"]
    assert "judge_funded" not in r.json()["artifacts"]  # BYOK path, not judge-funded
    assert ratelimit.remaining(config.judge_daily_cap()) == config.judge_daily_cap()  # cap untouched
    app.dependency_overrides.clear()


def test_over_daily_cap_falls_back_to_fixture(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    monkeypatch.setattr(config, "judge_key", lambda: "jk-secret")
    monkeypatch.setattr(config, "judge_daily_cap", lambda: 0)  # no judge budget today
    ratelimit.reset()
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate")  # no key, no budget -> fixtures
    assert r.status_code == 200 and calls == []  # live pipeline NOT run
    assert "judge_funded" not in r.json()["artifacts"]
    app.dependency_overrides.clear()
