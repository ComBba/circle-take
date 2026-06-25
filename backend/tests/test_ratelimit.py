"""Daily judge-run cap (in-memory soft cap)."""
from app import ratelimit


def test_try_consume_respects_cap(monkeypatch):
    monkeypatch.setattr(ratelimit, "_today", lambda: "2026-06-25")
    ratelimit.reset()
    assert ratelimit.try_consume(2) is True
    assert ratelimit.try_consume(2) is True
    assert ratelimit.try_consume(2) is False  # cap reached
    assert ratelimit.remaining(2) == 0


def test_resets_on_new_day(monkeypatch):
    ratelimit.reset()
    monkeypatch.setattr(ratelimit, "_today", lambda: "2026-06-25")
    assert ratelimit.try_consume(1) is True
    assert ratelimit.try_consume(1) is False
    monkeypatch.setattr(ratelimit, "_today", lambda: "2026-06-26")
    assert ratelimit.remaining(1) == 1  # fresh day, fresh cap
    assert ratelimit.try_consume(1) is True
