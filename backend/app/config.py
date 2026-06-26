"""App configuration + .env loading.

Loads .env.local (secrets, gitignored) then .env (policy-reserved) so uvicorn and
scripts see QWEN/Alibaba config. APP_ENV gates fixture vs live behavior. Import this
module first in main.py so the env is populated before qwen_client reads it.
"""
from __future__ import annotations

import contextvars
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _ROOT = Path(__file__).resolve().parents[2]  # circle-take/
    load_dotenv(_ROOT / ".env.local")
    load_dotenv(_ROOT / ".env")
except Exception:  # pragma: no cover - dotenv optional
    pass

# BYOK: the caller's Qwen key for the current request only. Set per request from the
# X-Qwen-Key header (config.set_request_key), read by qwen_client/video_tasks at call
# time, and never stored or logged. ContextVar => isolated per request/thread.
_request_qwen_key: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_qwen_key", default=""
)


def set_request_key(key: str | None) -> None:
    _request_qwen_key.set((key or "").strip())


def qwen_key() -> str:
    """Key to use now: the per-request BYOK key if present, else the env key (scripts)."""
    k = _request_qwen_key.get()
    if k and k != "replace_me":
        return k
    env = os.getenv("QWEN_API_KEY", "")
    return env if env and env != "replace_me" else ""


def app_env() -> str:
    return os.getenv("APP_ENV", "fixture")


def has_qwen_key() -> bool:
    key = os.getenv("QWEN_API_KEY", "")
    return bool(key) and key != "replace_me"


def is_live() -> bool:
    """Live mode requires APP_ENV=live and a real env key; otherwise use fixtures."""
    return app_env() == "live" and has_qwen_key()


def is_live_request() -> bool:
    """Run the real pipeline only in live mode AND when a key is available (BYOK or env)."""
    return app_env() == "live" and bool(qwen_key())


def gate_threshold() -> int:
    """Anchor Gate pass threshold — every score (identity/style/prop) must meet it.
    Env-tunable (CIRCLE_TAKE_GATE_THRESHOLD); set empirically in the live spike."""
    try:
        return int(os.getenv("CIRCLE_TAKE_GATE_THRESHOLD", "85"))
    except ValueError:
        return 85


def reference_image_url() -> str:
    """URL of the locked identity reference keyframe used to condition the reshoot.
    Empty until a Reference Pack keyframe is generated/hosted (then the reshoot is
    reference-conditioned instead of a blind t2v)."""
    return os.getenv("CIRCLE_TAKE_REFERENCE_URL", "").strip()


def judge_key() -> str:
    """Server-side judge key (the owner's) for the capped judge live path — lets judges
    see real Qwen+Wan without their own key. Empty disables it. Used only inside the
    per-request ContextVar; never stored in artifacts, returned, or logged."""
    k = os.getenv("JUDGE_QWEN_KEY", "").strip()
    return "" if k in ("", "replace_me") else k


def judge_daily_cap() -> int:
    """Max free judge live runs/day funded by the owner's key (soft cost cap)."""
    try:
        return int(os.getenv("JUDGE_DAILY_CAP", "10"))
    except ValueError:
        return 10


def judge_code() -> str:
    """Shared passcode that gates the judge-live path — published to judges (e.g. in the
    Devpost testing instructions) so only they, not the public, can spend the owner's key.
    Empty disables the judge-live path entirely (BYOK + fixtures only)."""
    return os.getenv("JUDGE_CODE", "").strip()
