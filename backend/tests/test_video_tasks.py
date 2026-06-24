import json

import httpx
import pytest
from app import video_tasks as vt


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_create_task_returns_id(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers.get("X-DashScope-Async") == "enable"
        assert "video-synthesis" in str(req.url)
        return httpx.Response(200, json={"output": {"task_id": "task-1"}})

    assert vt.create_task("a clay cat waves", client=_client(handler)) == "task-1"


def test_create_task_missing_id_raises(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")
    handler = lambda req: httpx.Response(200, json={"output": {}})
    with pytest.raises(vt.VideoError):
        vt.create_task("x", client=_client(handler))


def test_poll_until_succeeded(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")
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
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "")  # BYOK: no key available
    with pytest.raises(vt.VideoError):
        vt.create_task("x")


# --- submit_video: per-mode endpoint + input/parameters shape (the reshoot path) ---

def _capture(check):
    """MockTransport that runs check(body, url) on the request, then returns a task_id."""

    def handler(req: httpx.Request) -> httpx.Response:
        check(json.loads(req.content), str(req.url))
        return httpx.Response(200, json={"output": {"task_id": "t-ok"}})

    return _client(handler)


def test_submit_i2v_uses_resolution_and_img_url(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")

    def check(body, url):
        assert "video-generation/video-synthesis" in url
        assert body["parameters"].get("resolution") == "720P"
        assert "size" not in body["parameters"]
        assert body["input"]["img_url"] == "https://ref/luna.png"

    assert (
        vt.submit_video(
            "i2v", "luna waves", model="wan2.7-i2v",
            img_url="https://ref/luna.png", client=_capture(check),
        )
        == "t-ok"
    )


def test_submit_kf2v_uses_image2video_endpoint_and_resolution(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")

    def check(body, url):
        assert "image2video/video-synthesis" in url  # kf2v uses the other endpoint
        assert body["parameters"].get("resolution") == "720P"
        assert body["input"]["first_frame_url"] == "https://ref/a.png"
        assert body["input"]["last_frame_url"] == "https://ref/b.png"

    assert (
        vt.submit_video(
            "kf2v", "morph", model="wan2.2-kf2v-flash",
            first_frame_url="https://ref/a.png", last_frame_url="https://ref/b.png",
            client=_capture(check),
        )
        == "t-ok"
    )


def test_submit_r2v_uses_size_and_reference_urls(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")

    def check(body, url):
        assert "video-generation/video-synthesis" in url
        assert body["parameters"].get("size") == "1280*720"
        assert "resolution" not in body["parameters"]
        assert body["input"]["reference_urls"] == ["https://ref/luna.png"]

    assert (
        vt.submit_video(
            "r2v", "character1 hides the ad", model="wan2.7-r2v",
            reference_urls=["https://ref/luna.png"], client=_capture(check),
        )
        == "t-ok"
    )


def test_submit_vace_uses_function_and_ref_images(monkeypatch):
    monkeypatch.setattr(vt.config, "qwen_key", lambda: "k")

    def check(body, url):
        assert body["input"]["function"] == "image_reference"
        assert body["input"]["ref_images_url"] == ["https://ref/luna.png"]
        assert body["parameters"].get("size") == "1280*720"

    assert (
        vt.submit_video(
            "vace", "fix shot S02", model="wan2.1-vace-plus",
            function="image_reference", ref_images_url=["https://ref/luna.png"],
            client=_capture(check),
        )
        == "t-ok"
    )
