import pytest
from pydantic import BaseModel

from app import qwen_client


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
    monkeypatch.setattr(qwen_client, "QWEN_API_KEY", "")
    with pytest.raises(qwen_client.QwenError):
        qwen_client.chat_raw([{"role": "user", "content": "hi"}])
