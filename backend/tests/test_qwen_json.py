import pytest
from app import qwen_client
from pydantic import BaseModel


class Demo(BaseModel):
    verdict: str
    shots: int


def test_extract_json_from_fences():
    assert qwen_client._extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_surrounding_prose():
    assert qwen_client._extract_json('Sure, here: {"a": 1} done.') == {"a": 1}


def test_qwen_json_validates(monkeypatch):
    monkeypatch.setattr(
        qwen_client, "chat_raw",
        lambda *a, **k: '```json\n{"verdict": "fail", "shots": 4}\n```',
    )
    out = qwen_client.qwen_json("sys", "user", Demo)
    assert out.verdict == "fail" and out.shots == 4


def test_qwen_json_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake(messages, **k):
        calls["n"] += 1
        return "not json at all" if calls["n"] == 1 else '{"verdict": "pass", "shots": 3}'

    monkeypatch.setattr(qwen_client, "chat_raw", fake)
    out = qwen_client.qwen_json("s", "u", Demo, retries=1)
    assert out.shots == 3 and calls["n"] == 2


def test_qwen_json_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(qwen_client, "chat_raw", lambda *a, **k: "garbage, no json")
    with pytest.raises(qwen_client.QwenError):
        qwen_client.qwen_json("s", "u", Demo, retries=1)


def test_chat_raw_requires_key(monkeypatch):
    monkeypatch.setattr(qwen_client.config, "qwen_key", lambda: "")  # BYOK: no key available
    with pytest.raises(qwen_client.QwenError):
        qwen_client.chat_raw([{"role": "user", "content": "hi"}])


class _FakeResp:
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": "{}"}}]}


def _capture_payload(monkeypatch):
    """Patch httpx so chat_raw runs without network; return the captured request body."""
    captured = {}

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, headers=None, json=None):
            captured.update(json)
            return _FakeResp()

    monkeypatch.setattr(qwen_client.config, "qwen_key", lambda: "k")
    monkeypatch.setattr(qwen_client.httpx, "Client", _Client)
    return captured


def test_chat_raw_sends_enable_thinking_when_set(monkeypatch):
    payload = _capture_payload(monkeypatch)
    qwen_client.chat_raw([{"role": "user", "content": "hi"}], enable_thinking=False)
    assert payload["enable_thinking"] is False


def test_chat_raw_omits_enable_thinking_by_default(monkeypatch):
    payload = _capture_payload(monkeypatch)
    qwen_client.chat_raw([{"role": "user", "content": "hi"}])
    assert "enable_thinking" not in payload


def test_qwen_json_defaults_thinking_off(monkeypatch):
    # Text extraction must run thinking-off (7x faster; the generate-latency fix).
    seen = {}
    monkeypatch.setattr(
        qwen_client, "chat_raw",
        lambda messages, **k: seen.update(k) or '{"verdict": "x", "shots": 1}',
    )
    qwen_client.qwen_json("s", "u", Demo)
    assert seen.get("enable_thinking") is False


def test_qwen_vision_json_keeps_thinking(monkeypatch):
    # Vision verdicts (Continuity Court / Anchor Gate) keep thinking ON — proven 95/95/95.
    seen = {}
    monkeypatch.setattr(
        qwen_client, "chat_raw",
        lambda messages, **k: seen.update(k) or '{"verdict": "x", "shots": 1}',
    )
    qwen_client.qwen_vision_json("s", "data:image/png;base64,AAAA", "u", Demo)
    assert seen.get("enable_thinking") is None
