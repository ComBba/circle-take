"""Cross-dialect proof: the same Store contract works on Postgres.

Skipped unless TEST_DATABASE_URL points at a Postgres instance, so CI stays
SQLite-only and green. Run locally against a throwaway docker Postgres:

    docker run -d --rm -e POSTGRES_PASSWORD=pw -p 55432:5432 postgres:17
    TEST_DATABASE_URL='postgresql://postgres:pw@localhost:55432/postgres' \
        python -m pytest tests/test_store_postgres.py -v
"""
import os

import pytest
from app.store import Store

TEST_DB = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DB, reason="set TEST_DATABASE_URL to run the Postgres roundtrip"
)


def test_postgres_roundtrip():
    s = Store(TEST_DB)
    eid = s.create_episode("PG Episode", "DRAFT")

    ep = s.get_episode(eid)
    assert ep is not None and ep["title"] == "PG Episode" and ep["state"] == "DRAFT"

    s.put_artifact(eid, "brief", {"title": "X"})
    assert s.get_artifact(eid, "brief") == {"title": "X"}
    s.put_artifact(eid, "brief", {"title": "Y"})  # upsert, not duplicate
    assert s.get_episode(eid)["artifacts"]["brief"] == {"title": "Y"}

    s.update_status(eid, "CONTRACTED")
    assert s.get_episode(eid)["state"] == "CONTRACTED"

    assert s.get_episode("nope") is None
    assert s.get_artifact(eid, "missing") is None
