import httpx
import pytest

from app import video_tasks as vt


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_create_task_returns_id(monkeypatch):
    monkeypatch.setattr(vt, "QWEN_API_KEY", "k")

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers.get("X-DashScope-Async") == "enable"
        assert "video-synthesis" in str(req.url)
        return httpx.Response(200, json={"output": {"task_id": "task-1"}})

    assert vt.create_task("a clay cat waves", client=_client(handler)) == "task-1"


def test_create_task_missing_id_raises(monkeypatch):
    monkeypatch.setattr(vt, "QWEN_API_KEY", "k")
    handler = lambda req: httpx.Response(200, json={"output": {}})
    with pytest.raises(vt.VideoError):
        vt.create_task("x", client=_client(handler))


def test_poll_until_succeeded(monkeypatch):
    monkeypatch.setattr(vt, "QWEN_API_KEY", "k")
    seq = [
        {"output": {"task_status": "PENDING"}},
        {"output": {"task_status": "RUNNING"}},
        {"output": {"task_status": "SUCCEEDED", "video_url": "http://v/x.mp4"}},
    ]
    calls = {"n": 0}

    def fake_get(task_id, client=None):
        i = calls["n"]
        calls["n"] += 1
        return seq[i]

    monkeypatch.setattr(vt, "get_task", fake_get)
    url = vt.poll("task-1", interval=0, sleep=lambda s: None)
    assert url == "http://v/x.mp4"
    assert calls["n"] == 3


def test_poll_failed_raises(monkeypatch):
    monkeypatch.setattr(vt, "get_task", lambda *a, **k: {"output": {"task_status": "FAILED"}})
    with pytest.raises(vt.VideoError):
        vt.poll("t", sleep=lambda s: None)


def test_poll_timeout_raises(monkeypatch):
    monkeypatch.setattr(vt, "get_task", lambda *a, **k: {"output": {"task_status": "RUNNING"}})
    with pytest.raises(vt.VideoError):
        vt.poll("t", interval=1, max_wait=2, sleep=lambda s: None)


def test_create_requires_key(monkeypatch):
    monkeypatch.setattr(vt, "QWEN_API_KEY", "")
    with pytest.raises(vt.VideoError):
        vt.create_task("x")
