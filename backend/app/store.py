"""SQLite persistence for episodes and their artifacts.

Single-file store; one row per episode plus a key/value artifact table holding
JSON blobs (contracts, verdicts, memory, report). See docs/PLAN.md Phase 1.2.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from typing import Any, Optional

DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./circle_take.db")


def _resolve_path(database_url: Optional[str]) -> str:
    url = database_url or DEFAULT_DATABASE_URL
    return url[len("sqlite:///"):] if url.startswith("sqlite:///") else url


class Store:
    def __init__(self, db_path: Optional[str] = None):
        self.path = db_path or _resolve_path(None)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS episodes ("
                "id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS artifacts ("
                "episode_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, "
                "PRIMARY KEY (episode_id, key))"
            )

    def create_episode(self, title: str, state: str) -> str:
        eid = "ep" + uuid.uuid4().hex[:8]
        with self._conn() as c:
            c.execute(
                "INSERT INTO episodes (id, title, state) VALUES (?, ?, ?)",
                (eid, title, state),
            )
        return eid

    def get_episode(self, eid: str) -> Optional[dict]:
        with self._conn() as c:
            row = c.execute(
                "SELECT id, title, state FROM episodes WHERE id = ?", (eid,)
            ).fetchone()
            if row is None:
                return None
            arts = {
                r["key"]: json.loads(r["value"])
                for r in c.execute(
                    "SELECT key, value FROM artifacts WHERE episode_id = ?", (eid,)
                )
            }
            return {
                "episode_id": row["id"],
                "title": row["title"],
                "state": row["state"],
                "artifacts": arts,
            }

    def update_status(self, eid: str, state: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE episodes SET state = ? WHERE id = ?", (state, eid))

    def put_artifact(self, eid: str, key: str, value: Any) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO artifacts (episode_id, key, value) VALUES (?, ?, ?) "
                "ON CONFLICT(episode_id, key) DO UPDATE SET value = excluded.value",
                (eid, key, json.dumps(value)),
            )

    def get_artifact(self, eid: str, key: str) -> Any:
        with self._conn() as c:
            row = c.execute(
                "SELECT value FROM artifacts WHERE episode_id = ? AND key = ?",
                (eid, key),
            ).fetchone()
            return json.loads(row["value"]) if row else None
