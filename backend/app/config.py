"""App configuration + .env loading.

Loads .env.local (secrets, gitignored) then .env (policy-reserved) so uvicorn and
scripts see QWEN/Alibaba config. APP_ENV gates fixture vs live behavior. Import this
module first in main.py so the env is populated before qwen_client reads it.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _ROOT = Path(__file__).resolve().parents[2]  # circle-take/
    load_dotenv(_ROOT / ".env.local")
    load_dotenv(_ROOT / ".env")
except Exception:  # pragma: no cover - dotenv optional
    pass


def app_env() -> str:
    return os.getenv("APP_ENV", "fixture")


def has_qwen_key() -> bool:
    key = os.getenv("QWEN_API_KEY", "")
    return bool(key) and key != "replace_me"


def is_live() -> bool:
    """Live mode requires APP_ENV=live and a real key; otherwise use fixtures."""
    return app_env() == "live" and has_qwen_key()
