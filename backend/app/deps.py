"""Dependency providers. Tests override get_store with a temp-DB Store."""
from __future__ import annotations

from functools import lru_cache

from .store import Store


@lru_cache(maxsize=1)
def _default_store() -> Store:
    return Store()  # path from DATABASE_URL env (default ./circle_take.db)


def get_store() -> Store:
    return _default_store()
