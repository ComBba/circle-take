"""Daily cap for the server-side judge live path (soft, in-memory).

Bounds how many free judge live runs the owner's key funds per day, so a public
"run it live" button can't drain credits. The deploy is single-instance
(--max-instances 1), so process-global is instance-global; the count resets on restart.
This is a soft cost cap, not a security control.
"""
from __future__ import annotations

import datetime
import threading

_lock = threading.Lock()
_state: dict = {"day": None, "count": 0}


def _today() -> str:
    return datetime.date.today().isoformat()


def try_consume(cap: int) -> bool:
    """Reserve one judge run for today if under the cap. Returns True if allowed."""
    with _lock:
        today = _today()
        if _state["day"] != today:
            _state["day"], _state["count"] = today, 0
        if _state["count"] >= cap:
            return False
        _state["count"] += 1
        return True


def remaining(cap: int) -> int:
    """Judge runs left for today (without consuming)."""
    with _lock:
        if _state["day"] != _today():
            return cap
        return max(0, cap - _state["count"])


def reset() -> None:
    """Clear the counter (test helper / manual reset)."""
    with _lock:
        _state["day"], _state["count"] = None, 0
