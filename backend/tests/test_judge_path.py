"""Passcode-gated, capped judge-live path: BYOK > valid-passcode judge key > fixture.

The judge key and the passcode never leak into responses; the public (no/wrong code)
cannot spend the owner's key.
"""
import os
import tempfile

from app import config, pipeline, ratelimit
from app.deps import get_store
from app.main import app
from app.store import Store
from fastapi.testclient import TestClient

CODE = "judge-2026"


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


def _judge_on(monkeypatch):
    """Enable the judge path; make liveness depend only on the per-request key (ignore the
    .env.local key that config would otherwise see), so funded vs. fixture is observable."""
    monkeypatch.setattr(config, "judge_key", lambda: "jk-secret")
    monkeypatch.setattr(config, "judge_code", lambda: CODE)
    monkeypatch.setattr(config, "app_env", lambda: "live")
    monkeypatch.setattr(config, "qwen_key", lambda: config._request_qwen_key.get())
    ratelimit.reset()


def test_correct_passcode_funds_live(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    _judge_on(monkeypatch)
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate", headers={"X-Judge-Code": CODE})
    assert r.status_code == 200 and calls == ["text"]  # ran live
    assert r.json()["artifacts"]["judge_funded"] is True
    assert "jk-secret" not in r.text and CODE not in r.text  # neither key nor code leaks


def test_wrong_or_missing_passcode_gets_fixtures(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    _judge_on(monkeypatch)
    c = _client()
    # wrong code
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate", headers={"X-Judge-Code": "nope"})
    assert calls == [] and "judge_funded" not in r.json()["artifacts"]
    # no code at all
    eid2 = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r2 = c.post(f"/api/episodes/{eid2}/generate")
    assert calls == [] and "judge_funded" not in r2.json()["artifacts"]


def test_byok_overrides_passcode_and_leaves_cap_untouched(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    _judge_on(monkeypatch)
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate", headers={"X-Qwen-Key": "byok"})  # no code needed
    assert calls == ["text"] and "judge_funded" not in r.json()["artifacts"]
    assert ratelimit.remaining(config.judge_daily_cap()) == config.judge_daily_cap()  # cap untouched


def test_over_daily_cap_falls_back_to_fixture_even_with_code(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    _judge_on(monkeypatch)
    monkeypatch.setattr(config, "judge_daily_cap", lambda: 0)  # no budget today
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate", headers={"X-Judge-Code": CODE})
    assert calls == [] and "judge_funded" not in r.json()["artifacts"]


def test_judge_path_off_without_passcode_configured(monkeypatch):
    calls = []
    _stub_pipeline(monkeypatch, calls)
    _judge_on(monkeypatch)
    monkeypatch.setattr(config, "judge_code", lambda: "")  # JUDGE_CODE unset -> path disabled
    c = _client()
    eid = c.post("/api/episodes", json={"title": "Live"}).json()["episode_id"]
    r = c.post(f"/api/episodes/{eid}/generate", headers={"X-Judge-Code": CODE})
    assert calls == [] and "judge_funded" not in r.json()["artifacts"]  # off, even with a code sent
